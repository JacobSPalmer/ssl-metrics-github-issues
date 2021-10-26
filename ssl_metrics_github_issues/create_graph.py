from argparse import ArgumentParser, Namespace
from datetime import datetime
from json import load
from os.path import exists
from typing import Any, KeysView

import matplotlib.pyplot as plt
from dateutil.parser import parse
from intervaltree import IntervalTree
from matplotlib.figure import Figure
from progress.bar import Bar


def get_argparse() -> Namespace:
    parser: ArgumentParser = ArgumentParser(
        prog="Graph GitHub Issues",
        usage="This program outputs a series of graphs based on GitHub issue data.",
    )
    parser.add_argument(
        "-c",
        "--closed-issues-graph-filename",
        help="The filename of the output graph of closed issues",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-i",
        "--input",
        help="The input JSON file that is to be used for graphing",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-o",
        "--open-issues-graph-filename",
        help="The filename of the output graph of open issues",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-x",
        "--joint-graph-filename",
        help="The filename of the joint output graph of open and closed issues",
        type=str,
        required=True,
    )

    return parser.parse_args()


def loadJSON(filename: str = "issues.json") -> list:
    with open(file=filename, mode="r") as jsonFile:
        return load(jsonFile)


def createIntervalTree(data: list, filename: str = "issues.json") -> IntervalTree:
    tree: IntervalTree = IntervalTree()
    day0: datetime = parse(data[0]["created_at"]).replace(tzinfo=None)

    with Bar(f"Creating interval tree from {filename}... ", max=len(data)) as pb:
        for issue in data:
            createdDate: datetime = parse(issue["created_at"]).replace(tzinfo=None)

            if issue["state"] == "closed":
                closedDate: datetime = parse(issue["closed_at"]).replace(tzinfo=None)
            else:
                closedDate: datetime = datetime.now(tz=None)

            begin: int = (createdDate - day0).days
            end: int = (closedDate - day0).days

            try:
                issue["endDayOffset"] = 0
                tree.addi(begin=begin, end=end, data=issue)
            except ValueError:
                issue["endDayOffset"] = 1
                tree.addi(begin=begin, end=end + 1, data=issue)

            pb.next()

    return tree


def issue_spoilage_data(
        data: IntervalTree, filename: str = "issue_spoilage.json"
):
    startDay: int = data.begin()
    endDay: int = data.end()
    list_of_spoilage_values = []
    for i in range(endDay - 1):
        temp_overlap = data.overlap(i - 1, i)
        proc_overlap = []
        for issue in temp_overlap:
            if issue.data["state"] == "open":
                proc_overlap.append(issue)
            elif issue.begin != issue.end - 1 and issue.data["endDayOffset"] != 1:
                proc_overlap.append(issue)
        list_of_spoilage_values.append({"day": i, "number_open": len(proc_overlap)})
    return list_of_spoilage_values

def plot_OpenIssuesPerDay_Line(
    pregeneratedData: dict = None,
    filename: str = "open_issues_per_day_line.png",
):
    figure: Figure = plt.figure()

    plt.title("Number of Open Issues Per Day")
    plt.ylabel("Number of Issues")
    plt.xlabel("Day")

    data: dict = pregeneratedData

    plt.plot(data.keys(), data.values())
    figure.savefig(filename)

    return exists(filename)


def plot_ClosedIssuesPerDay_Line(
    pregeneratedData: dict = None,
    filename: str = "closed_issues_per_day_line.png",
):
    figure: Figure = plt.figure()

    plt.title("Number of Closed Issues Per Day")
    plt.ylabel("Number of Issues")
    plt.xlabel("Day")

    data: dict = pregeneratedData

    plt.plot(data.keys(), data.values())
    figure.savefig(filename)

    return exists(filename)


def plot_OpenClosedIssuesPerDay_Line(
    pregeneratedData_OpenIssues: dict = None,
    pregeneratedData_ClosedIssues: dict = None,
    filename: str = "open_closed_issues_per_day_line.png",
):
    figure: Figure = plt.figure()

    plt.title("Number of Issues Per Day")
    plt.ylabel("Number of Issues")
    plt.xlabel("Day")

    openData: dict = pregeneratedData_OpenIssues
    closedData: dict = pregeneratedData_ClosedIssues

    plt.plot(openData.keys(), openData.values(), color="blue", label="Open Issues")
    plt.plot(closedData.keys(), closedData.values(), color="red", label="Closed Issues")
    plt.legend()

    figure.savefig(filename)

    return exists(filename)

def plot_IssueSpoilage(
        spoilage_data : list
):
    figure: Figure = plt.figure()

    plt.title("Number of Issues Per Day")
    plt.ylabel("Number of Issues")
    plt.xlabel("Day")

    plt.plot(spoilage_data)
    figure.show();



def fillDictBasedOnKeyValue(
    dictionary: dict, tree: IntervalTree, key: str, value: Any
) -> dict:
    data: dict = {}
    keys: KeysView = dictionary.keys()

    maxKeyValue: int = max(keys)
    minKeyValue: int = min(keys)

    with Bar(
        f'Getting the total number of "{key} = {value}" issues per day... ',
        max=maxKeyValue,
    ) as pb:
        for x in range(minKeyValue, maxKeyValue):
            try:
                data[x] = dictionary[x]
            except KeyError:
                count = 0
                interval: IntervalTree
                for interval in tree.at(x):
                    if interval.data[key] == value:
                        count += 1
                data[x] = count

            pb.next()

    return data


def main() -> None:
    args: Namespace = get_argparse()

    if args.input[-5::] != ".json":
        print("Invalid input file type. Input file must be JSON")
        quit(1)

    jsonData: list = loadJSON(filename=args.input)

    tree: IntervalTree = createIntervalTree(data=jsonData, filename=args.input)

    startDay: int = tree.begin()
    endDay: int = tree.end()

    if len(tree.at(endDay)) == 0:
        endDay -= 1

    baseDict: dict = {startDay: len(tree.at(startDay)), endDay: len(tree.at(endDay))}

    openIssues: dict = fillDictBasedOnKeyValue(
        dictionary=baseDict, tree=tree, key="state", value="open"
    )

    closedIssues: dict = fillDictBasedOnKeyValue(
        dictionary=baseDict, tree=tree, key="state", value="closed"
    )

    plot_OpenIssuesPerDay_Line(
        pregeneratedData=openIssues, filename=args.open_issues_graph_filename
    )

    plot_ClosedIssuesPerDay_Line(
        pregeneratedData=closedIssues, filename=args.closed_issues_graph_filename
    )

    plot_OpenClosedIssuesPerDay_Line(
        pregeneratedData_ClosedIssues=closedIssues,
        pregeneratedData_OpenIssues=openIssues,
        filename=args.joint_graph_filename,
    )
    new_list = issue_spoilage_data(data=tree)
    print(new_list)
    # print(type(new_list))

if __name__ == "__main__":
    # main()
    json_input = loadJSON("issues_to_graph.json")
    i_t = createIntervalTree(json_input)
    spoilage_data = issue_spoilage_data(i_t)
    plot_IssueSpoilage(spoilage_data)


