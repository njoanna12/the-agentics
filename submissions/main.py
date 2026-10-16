"""CrewAI starter: a four-agent mechatronics concept team
(systems engineer -> mechanical designer -> quality control -> program lead).

Run:  uv run python main.py "your topic here"

CrewAI's big idea: you describe a TEAM of role-playing agents and the TASKS they
own. CrewAI handles passing each task's output to the next agent.
"""

import os
import sys
from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

load_dotenv()

# --- 1. The model --------------------------------------------------------
# CrewAI has no built-in Groq provider, but Groq speaks the OpenAI API, so we
# point CrewAI's OpenAI client at Groq's endpoint. Change GROQ_MODEL in .env
# to swap models without touching this file.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
llm = LLM(
    model=f"openai/{MODEL}",  # the leading "openai/" only selects the client
    base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.3,
)

# --- 2. The agents: WHO is on the team -----------------------------------

mechanical_designer = Agent(
    role="Mechanical Designer",
    goal="Given the concept {topic}, propose the physical design: overall "
         "form, structure, materials, and moving parts, with a few "
         "alternative approaches",
    backstory="You are a creative mechanical designer who sketches several "
              "options before committing to one. You think about how the "
              "thing is built, what it is made of, and how it survives its "
              "environment (water, heat, vibration, wear). You explain why "
              "you chose each option and say plainly when something is a "
              "guess.",
    llm=llm,
    allow_delegation=False,
)

systems_engineer = Agent(
    role="Systems Engineer",
    goal="Given the concept {topic}, map out how the whole system could work: "
         "the major subsystems, how they connect, and the key requirements "
         "and trade-offs",
    backstory="You think in big pictures and interfaces. You break an idea "
              "into mechanical, electrical, and software pieces, show how "
              "they depend on each other, and flag where choices in one area "
              "will cause problems in another. You separate must-haves from "
              "nice-to-haves.",
    llm=llm,
    allow_delegation=False,
)

quality_control = Agent(
    role="Quality Control Engineer",
    goal="Given the concept {topic}, identify what could go wrong, what "
         "needs to be tested, and which claims or assumptions in the plan "
         "are unsupported",
    backstory="You are skeptical by trade. You look at an idea and ask how "
              "it fails, how you would prove it works, and what standards "
              "or tests apply. You flag shaky assumptions, suggest concrete "
              "checks, and never let an unverified claim pass as fact.",
    llm=llm,
    allow_delegation=False,
)

program_lead = Agent(
    role="Program Lead",
    goal="Combine the whole team's work on {topic} into one coherent concept "
         "report a decision-maker can act on",
    backstory="You run the engineering program. You read every teammate's "
              "output, resolve contradictions between them, keep the "
              "quality engineer's warnings visible, and write a clear, "
              "well-organized final report. You never invent details the "
              "team did not produce.",
    llm=llm,
    allow_delegation=False,
)

# --- 3. The tasks: WHAT each person owns ---------------------------------

systems_task = Task(
    description="Brainstorm a quick system-level plan for the concept: {topic}. "
                "Name the major subsystems (mechanical, electrical, software), "
                "how they connect, 3 key requirements, and 1 major trade-off. "
                "Keep it under 250 words.",
    expected_output="A bulleted system overview, 250 words max.",
    agent=systems_engineer,
)

design_task = Task(
    description="Using the system overview, propose 2 alternative mechanical "
                "designs for {topic}. For each, give the form, main materials, "
                "and moving parts, then recommend one in a sentence. Mark "
                "guesses as assumptions. Keep it under 250 words.",
    expected_output="Two short design concepts and a recommended pick, "
                    "250 words max.",
    agent=mechanical_designer,
)

quality_task = Task(
    description="Review the system overview and mechanical designs for "
                "{topic}. List the top 3 failure risks, one test for each, "
                "and flag unsupported claims as [unverified]. Keep it under "
                "250 words.",
    expected_output="A short risk list with a test per risk and [unverified] "
                    "flags, 250 words max.",
    agent=quality_control,
)

report_task = Task(
    description="Compile a brief final concept report for {topic} from the "
                "systems overview, mechanical design, and quality review. "
                "Include a 2-sentence executive summary, one short paragraph "
                "per teammate, any conflicts between them, and 2 next steps. "
                "Keep every [unverified] flag. Keep it under 250 words total.",
    expected_output="A markdown report: Executive Summary, Systems, "
                    "Mechanical Design, Quality Risks, Conflicts, Next Steps. "
                    "250 words max.",
    agent=program_lead,
    context=[systems_task, design_task, quality_task],
)

# --- 4. The crew: HOW they work together ---------------------------------
crew = Crew(
    agents=[systems_engineer, mechanical_designer, quality_control, program_lead],
    tasks=[systems_task, design_task, quality_task, report_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or "building a rescue robot for high-risk environments"
    result = crew.kickoff(inputs={"topic": topic})

    out = Path("output")
    out.mkdir(exist_ok=True)
    (out / "explainer.md").write_text(result.raw, encoding="utf-8")
    print("\n=== FINAL OUTPUT (also saved to output/explainer.md) ===\n")
    print(result.raw)
