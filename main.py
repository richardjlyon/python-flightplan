# Main parsing logic

from conftest import data_path
from deserialisers.little_navmap import LittleNavmap
from route_processor.route_processor import ProcessorConfig, process_route


def main():
    # Load the plan
    file_path = data_path() / "VFR Newcastle (EGNT) to Inverness (EGPE).lnmpln"
    plan = LittleNavmap.read(file_path)

    # Proces the route
    waypoints = plan.Flightplan.Waypoints
    config = ProcessorConfig(id_entry=3, id_exit=12)
    processed_route_wps = process_route(waypoints, config)

    # Create new plan
    plan.Flightplan.Waypoints = processed_route_wps

    # Save to disk
    outfile = file_path.with_name(file_path.stem + " [formatted]" + file_path.suffix)
    plan.write(outfile)

    # Report
    print()
    for wp in processed_route_wps:
        print(
            f"{wp.Name if wp.Name else 'None':15} : {wp.Ident:13} : {wp.Pos.Alt:05} : {wp.Comment}"
        )


if __name__ == "__main__":
    main()
