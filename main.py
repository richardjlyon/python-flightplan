# Main parsing logic
def main():
    pass
    # current_dir = Path(__file__).parent
    # test_file_path = (
    #     current_dir
    #     / "tests"
    #     / "data"
    #     / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    # )
    #
    # # Read the XML file
    # with open(test_file_path, "r", encoding="utf-8") as file:
    #     xml_content = file.read()
    #
    # # Parse XML to a dictionary
    # xml_dict = xmltodict.parse(xml_content)
    #
    # # Extract "LittleNavmap" as root
    # data = xml_dict["LittleNavmap"]
    #
    # # Deserialize into the LittleNavmap Pydantic model
    # navmap = LittleNavmap(**data)
    #
    # # Modify waypoint 1 name
    # navmap.Flightplan.Waypoints[1].Ident = "BOLLOCKS"
    # # Pretty print the deserialized model
    # pprint(navmap.model_dump(), indent=2, width=120, depth=None)
    #
    # output_file_path = current_dir / "test.lnmpln"
    # serialized_xml = serialize_to_xml(navmap)
    # with open(output_file_path, "w") as f:
    #     f.write(serialized_xml)


if __name__ == "__main__":
    main()
