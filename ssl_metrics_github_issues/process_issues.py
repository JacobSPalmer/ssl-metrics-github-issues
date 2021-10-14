import json

# TODO specify from _ import _
import pathlib
from argparse import ArgumentParser, Namespace
from os.path import exists
from datetime import datetime
from dateutil.parser import parse


def get_argparse() -> Namespace:
    parser: ArgumentParser = ArgumentParser(
        prog="GH Issue Engagement",
        usage="This program generates JSON file containing specific data related to a repositories issue engagement.",
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Raw repository issues json file to be used. These files can be generated using the "
        "ssl-metrics-github-issues tool.",
        default="issues.json",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-s",
        "--save-json",
        help="Specify name to save analysis to JSON file.",
        default="issue_engagement.json",
        type=str,
        required=True,
    )
    return parser.parse_args()


def getIssueEngagementReport(
    input_json: str,
) -> list:

    with open(input_json, "r") as json_file:
        # with open("issues.json") as json_file:
        data = json.load(json_file)
        data = [
            dict(
                issue_number=k1["number"],
                comments=k1["comments"],
                created_at=k1["created_at"],
                closed_at=k1["closed_at"],
                state=k1["state"],
            )
            for k1 in data
        ]
        json_file.close()

    removal_List = []

    for issue in data:
        createdDate: datetime = parse(issue["created_at"]).replace(tzinfo=None)
        today: datetime = datetime.now(tz=None)
        if (today - createdDate).days > 40: # TODO: Make this into a command line arg for a window of time
            removal_List.append(issue)

    for issue in removal_List:
        data.remove(issue)

    return data


def storeJSON(
    issues: list,
    output_file: str,
) -> bool:
    # json.dump(issues)
    data = json.dumps(issues)
    with open(file=output_file, mode="w") as json_file:
        json_file.write(data)
    return exists(output_file)


def main() -> None:
    args: Namespace = get_argparse()

    issues_json = getIssueEngagementReport(
        input_json=args.input,
    )

    storeJSON(
        issues=issues_json,
        output_file=args.save_json,
    )


if __name__ == "__main__":
    main()
