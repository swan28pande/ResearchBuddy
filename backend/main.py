import queue
from workflows.research_workflow import build_and_run_workflow

def main():

    query = input("Enter your research query: ")
    report = build_and_run_workflow(query)
    print(report)

if __name__ == "__main__":
    main()