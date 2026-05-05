import xmltodict


def load_touren(xml_path: str) -> list[dict]:
    """Load tour data from a Kompass XML file.

    Args:
        xml_path (str): Path to the Kompass XML file.

    Returns:
        list[dict]: A list of dictionaries containing tour data.
    """
    with open(xml_path, "r", encoding="utf-8") as file:
        xml_content = file.read()

    result_dict = xmltodict.parse(
        xml_content,
        dict_constructor=dict,
        force_list=("tour", "Bild", "poi", "chapters", "content"),
    )

    touren = [t.get("german") for t in result_dict["buch"].get("tour", {})]
    return touren
