"""CLI entrypoint for running the resume screening pipeline."""

import argparse
from pathlib import Path

from src.pipeline import ResumeScreeningPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run resume screening, scoring, and ranking against a target role."
    )
    parser.add_argument(
        "--resumes",
        default="data/raw/resumes_sample.csv",
        help="Path to resumes CSV/JSON with candidate_name and resume_text columns.",
    )
    parser.add_argument(
        "--job",
        default="data/raw/job_description_data_scientist.txt",
        help="Path to a text file containing the target job description.",
    )
    parser.add_argument(
        "--role",
        default="data_scientist",
        help="Role key to apply configured required and important skill weights.",
    )
    parser.add_argument(
        "--output",
        default="data/processed",
        help="Output folder for ranking and summary artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pipeline = ResumeScreeningPipeline()
    artifacts = pipeline.run(
        resumes_path=args.resumes,
        job_description_path=args.job,
        role=args.role,
        output_dir=args.output,
    )

    print("Resume screening complete.")
    print(f"Ranking file: {artifacts['ranking']}")
    print(f"Summary file: {artifacts['summary']}")


if __name__ == "__main__":
    main()
