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
    config = ProcessorConfig(id_entry=2, id_exit=-2)
    processed_route_wps = process_route(waypoints, config)

    # Create new plan
    plan.Flightplan.Waypoints = processed_route_wps

    # Save to disk
    outfile = data_path() / "processed.lnmpln"
    plan.write(outfile)

    # Report
    print()
    for wp in processed_route_wps:
        print(f"{wp.Name} : {wp.Ident}")


if __name__ == "__main__":
    main()
