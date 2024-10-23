from pydantic import ConfigDict

model_config = ConfigDict(
    use_enum_values = True,
    arbitrary_types_allowed=True
)

