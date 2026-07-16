"""Generate a deterministic corpus of entirely fictional CVs."""

from io import BytesIO
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus import Image as PdfImage

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "cvs"
PORTRAITS = Path(__file__).parent / "assets" / "synthetic_portraits.png"

NAMES = [
    "Sofia Marin",
    "Kwame Mensah",
    "Elena Fischer",
    "Kenji Nakamura",
    "Leyla Demir",
    "David Romero",
    "Arjun Patel",
    "Maeve O'Connor",
    "Javier Costa",
    "Amara Okafor",
    "Liam Bennett",
    "Mei Lin",
    "Astrid Nielsen",
    "Malik Johnson",
    "Clara Moreau",
    "Mateo Silva",
    "Priya Shah",
    "Thomas Keller",
    "Daniel Kim",
    "Nia Williams",
    "Erik Andersson",
    "Laura Bianchi",
    "Andre Baptiste",
    "Ines Carvalho",
    "Omar Haddad",
    "Noor Rahman",
    "Lucas Meyer",
    "Hannah Weber",
    "Min-jun Park",
    "Rosa Alvarez",
]
ROLES = [
    ("Senior Backend Engineer", ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]),
    ("Data Scientist", ["Python", "pandas", "scikit-learn", "SQL", "Experimentation"]),
    ("Frontend Engineer", ["TypeScript", "React", "Accessibility", "CSS", "Vitest"]),
    ("Machine Learning Engineer", ["Python", "PyTorch", "MLOps", "Kubernetes", "RAG"]),
    ("Product Manager", ["Product discovery", "Analytics", "Roadmaps", "A/B testing", "Agile"]),
    ("DevOps Engineer", ["Terraform", "AWS", "Kubernetes", "GitHub Actions", "Observability"]),
    (
        "UX Researcher",
        ["User interviews", "Usability testing", "Figma", "Research synthesis", "Accessibility"],
    ),
    ("Security Engineer", ["Threat modeling", "OAuth", "SIEM", "Python", "ISO 27001"]),
    ("Analytics Engineer", ["SQL", "dbt", "BigQuery", "Looker", "Data quality"]),
    ("Mobile Engineer", ["React Native", "TypeScript", "iOS", "Android", "Testing"]),
]
CITIES = [
    "Barcelona",
    "Lisbon",
    "Berlin",
    "Amsterdam",
    "Paris",
    "Madrid",
    "Dublin",
    "Copenhagen",
    "London",
    "Remote",
]
LANGUAGES = [
    "English (fluent), Spanish (native)",
    "English (fluent), French (professional)",
    "English (fluent), German (professional)",
    "English (fluent), Portuguese (native)",
    "English (fluent), Japanese (native)",
]
COMPANIES = [
    "Northstar Labs",
    "Blue Oak Systems",
    "Cedar Analytics",
    "Juniper Works",
    "Atlas Digital",
    "Bright River",
]
SCHOOLS = [
    "Fictional Institute of Technology",
    "Example University",
    "Northbridge School of Engineering",
    "Demo State University",
]


def candidate(index: int) -> dict[str, object]:
    role, skills = ROLES[index % len(ROLES)]
    start = 2011 + index % 8
    return {
        "name": NAMES[index],
        "role": role,
        "skills": skills,
        "city": CITIES[index % len(CITIES)],
        "languages": LANGUAGES[index % len(LANGUAGES)],
        "company": COMPANIES[index % len(COMPANIES)],
        "previous": COMPANIES[(index + 2) % len(COMPANIES)],
        "school": SCHOOLS[index % len(SCHOOLS)],
        "start": start,
        "email": f"candidate{index + 1:02d}@example.test",
    }


def portrait(index: int) -> BytesIO:
    sheet = Image.open(PORTRAITS)
    width, height = sheet.size
    col, row = index % 6, index // 6
    cell = sheet.crop(
        (col * width // 6, row * height // 5, (col + 1) * width // 6, (row + 1) * height // 5)
    )
    stream = BytesIO()
    cell.save(stream, "PNG")
    stream.seek(0)
    return stream


def render(index: int, data: dict[str, object]) -> Path:
    slug = str(data["name"]).lower().replace(" ", "_").replace("'", "")
    path = OUTPUT / f"cv_{index + 1:02d}_{slug}.pdf"
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13,
        textColor=colors.HexColor("#27364A"),
        spaceAfter=4,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#0A6470"),
        spaceBefore=8,
        spaceAfter=4,
    )
    title = ParagraphStyle(
        "Title",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=25,
        textColor=colors.HexColor("#15324B"),
    )
    role_style = ParagraphStyle(
        "Role", parent=body, fontSize=12, textColor=colors.HexColor("#0A6470")
    )
    story: list[object] = [
        PdfImage(portrait(index), width=32 * mm, height=32 * mm),
        Spacer(1, 2 * mm),
        Paragraph(str(data["name"]), title),
        Paragraph(str(data["role"]), role_style),
        Paragraph(f"{data['city']} · {data['email']} · +34 600 000 {index + 1:03d}", body),
        HRFlowable(color=colors.HexColor("#36A0A8"), thickness=1, spaceBefore=5, spaceAfter=4),
        Paragraph("SUMMARY", heading),
        Paragraph(
            f"Pragmatic {str(data['role']).lower()} with {2026 - int(data['start'])} years of experience delivering reliable digital products. Known for clear communication, measurable outcomes, and thoughtful collaboration across disciplines.",
            body,
        ),
        Paragraph("SKILLS", heading),
        Paragraph(" · ".join(data["skills"]), body),
        Paragraph("EXPERIENCE", heading),
        Paragraph(f"<b>{data['role']} — {data['company']}</b> | 2021–Present", body),
        Paragraph(
            f"Led initiatives using {data['skills'][0]}, {data['skills'][1]}, and {data['skills'][2]}; improved delivery predictability by {15 + index % 20}% and mentored cross-functional colleagues.",
            body,
        ),
        Paragraph(f"<b>Specialist — {data['previous']}</b> | {data['start']}–2021", body),
        Paragraph(
            "Owned discovery through delivery, introduced lightweight quality practices, and translated stakeholder needs into maintainable solutions.",
            body,
        ),
        Paragraph("EDUCATION", heading),
        Paragraph(f"MSc, Applied Technology — {data['school']}, {int(data['start']) - 1}", body),
        Paragraph("LANGUAGES", heading),
        Paragraph(str(data["languages"]), body),
        Spacer(1, 5 * mm),
        Paragraph(
            "This résumé and portrait are entirely synthetic and were created for a technical demonstration.",
            ParagraphStyle(
                "Foot", parent=body, fontSize=7, textColor=colors.grey, alignment=TA_LEFT
            ),
        ),
    ]
    SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"Fictional CV — {data['name']}",
        author="CV Screening Demo",
    ).build(story)
    return path


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT.glob("*.pdf"):
        old.unlink()
    paths = [render(i, candidate(i)) for i in range(30)]
    print(f"Generated {len(paths)} fictional CVs in {OUTPUT}")


if __name__ == "__main__":
    main()
