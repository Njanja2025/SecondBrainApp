# Blueprint export script for admin dashboard layout
# Generates a placeholder PNG and PDF using Pillow and reportlab

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# PNG export
img = Image.new("RGB", (1200, 800), color="#222")
draw = ImageDraw.Draw(img)
font = None
try:
    font = ImageFont.truetype("arial.ttf", 32)
except:
    font = ImageFont.load_default()
draw.text((50, 50), "SecondBrain Admin Dashboard Blueprint", fill="white", font=font)
draw.rectangle([40, 120, 1160, 760], outline="white", width=3)
draw.text((60, 140), "[Placeholder for dashboard layout blocks]", fill="white", font=font)
img.save("admin_dashboard_blueprint.png")

# PDF export
c = canvas.Canvas("admin_dashboard_blueprint.pdf", pagesize=letter)
c.setFont("Helvetica-Bold", 24)
c.drawString(72, 720, "SecondBrain Admin Dashboard Blueprint")
c.setStrokeColorRGB(1, 1, 1)
c.rect(60, 200, 480, 400, stroke=1, fill=0)
c.setFont("Helvetica", 14)
c.drawString(80, 580, "[Placeholder for dashboard layout blocks]")
c.save()

# Export embed-ready HTML widget (placeholder)
with open("admin_dashboard_widget.html", "w") as f:
    f.write("""
    <div style='width:600px;height:400px;border:2px solid #222;background:#111;color:#fff;font-family:sans-serif;padding:24px;'>
        <h2>SecondBrain Admin Dashboard Widget</h2>
        <p>[Embed-ready widget placeholder]</p>
    </div>
    """)

print("Exported admin_dashboard_blueprint.png and admin_dashboard_blueprint.pdf and admin_dashboard_widget.html")
