"""Handle folders that serve as a source for Merit settings"""

import pandas as pd

LOCATIONS = {
    "flex": "flex.csv",
    "interconnectors": "interconnectors.csv",
    "producers": "supply.csv",
    "users": "demand.csv",
}

VALID_PRODUCERS = [
    "MustRunProducer",
    "VolatileProducer",
    "CurveProducer",
    "DispatchableProducer",
]

# A list of flex types which may be specified in the flex.csv file mapped to their corresponding
# Merit participant types.
FLEX_TYPES = {
    "generic": "Merit::Flex::Base",
    "storage": "Merit::Flex::Storage",
}

CURVE_KEYS = ['availability_curve', 'load_profile']


class Source:
    """Class that helps with IO, generating merit order settings from supplied csvs"""

    def __init__(self, path):
        """
        Path path points to config folder
        Should we also add another argument to use an ETM scenario or dataset??
        """
        self.path = path
        self._validate()

    def producers(self):
        """
        Reads producers from the correct file

        Returns:
            Generator[dict]: producer settings
        """
        yield from self._clean_rows_from("producers")

    def users(self):
        """
        Reads users from the correct file

        Returns:
            Generator[dict]: user settings
        """
        yield from self._clean_rows_from("users")

    def interconnectors(self):
        """
        Reads users from the correct file

        Returns:
            Generator[dict]: user settings
        """
        yield from self._clean_rows_from("interconnectors")

    def flex(self):
        """
        Reads flex settings from the correct file

        Returns:
            Generator[dict]: flex settings
        """
        yield from self._clean_rows_from("flex")

    # Private ------------------------------------------------------------------

    def _validate(self):
        """Validates the presence of all files in the Source"""
        for _, location in LOCATIONS.items():
            if not (self.path / location).exists():
                raise MissingSourceError(f"Unable to locate {self.path / location}")

    def _read(self, location):
        """
        Reads the file at location into a pd.DataFrame

        Retruns:
            pd.Dataframe
        """
        try:
            df = pd.read_csv(self.path / LOCATIONS[location])

            if "path_to_load_profile" in df.columns:
                df.rename(
                    columns={"path_to_load_profile": "load_profile"}, inplace=True
                )

            return df
        except pd.errors.ParserError as exc:
            raise InvalidSourceError(
                f"{LOCATIONS[location]} could not be parsed: {exc}"
            ) from exc

    def _clean_rows_from(self, location):
        """
        Generates clean rows from a location

        Params:
            location(str): One of producers, users, interconnectors

        Returns:
            Generator[dict]: parameters
        """
        yield from (
            self._clean(row, location) for (_, row) in self._read(location).iterrows()
        )

    def _clean(self, row, location):
        """
        Clean up and validate the csv row

        Returns:
            dict[str,Any]: the row converted to useable params
        """
        self._validate_key(row, location)

        if location == "producers":
            self._validate_producer_row(row)
        elif location == "flex":
            if row["type"] not in FLEX_TYPES:
                raise InvalidSourceError(
                    f'Flex type {row["type"]} is not supported ({LOCATIONS["flex"]}: {row["key"]})'
                )

            row["type"] = FLEX_TYPES[row["type"]]

        # if "load_profile" in row and isinstance(row["load_profile"], str):
        self._set_curves(row)

        return row.dropna().to_dict()

    def _validate_key(self, row, location):
        if not row["key"]:
            raise InvalidSourceError(f'"key" cannot be empty ({LOCATIONS[location]})')

        if not row["key"].startswith(":"):
            row["key"] = f':{row["key"]}'

    def _validate_producer_row(self, row):
        """Check if producer type is supported"""
        if not row["type"] in VALID_PRODUCERS:
            raise InvalidSourceError(
                f'Type should be one of {VALID_PRODUCERS} ({LOCATIONS["producers"]}: {row["key"]})'
            )

    def _set_curves(self, row):
        """
        Extends curve paths, including path validation

        Params:
            row(pd.Series): The row we're iterating over
        """
        for key in (k for k in CURVE_KEYS if k in row and isinstance(row[k], str)):
            lpf_path = self.path / row[key]
            if not lpf_path.exists():
                raise InvalidSourceError(f"{key} could not be located ({lpf_path})")
            row[key] = lpf_path


class MissingSourceError(BaseException):
    """Source is missing!"""


class InvalidSourceError(BaseException):
    """Something is wrong in the source"""
