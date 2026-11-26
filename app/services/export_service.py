from io import BytesIO
from pathlib import Path
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def make_pdf(run):
    font = Path(__file__).resolve().parents[1]/'static/fonts/BeVietnamPro-Regular.ttf'
    pdfmetrics.registerFont(TTFont('Vietnamese',str(font)))
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = 'Vietnamese'
        style.leading = 17
    styles['Title'].textColor = colors.HexColor('#00558f')
    result = run.result
    output = BytesIO()
    story = [Paragraph('Lộ trình học tập cá nhân hóa',styles['Title']),Spacer(1,20),
        Paragraph(escape(result['career_name']),styles['Heading2']),
        Paragraph(escape(result['curriculum_name']+' · '+result['cohort']),styles['Normal']),
        Paragraph('Ngày xuất: '+datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%d/%m/%Y %H:%M'),styles['Normal']),
        Paragraph('Nguồn: '+escape(result['source'])+' · Học kỳ trong tài liệu là dự kiến.',styles['Normal']),
        Paragraph('Dữ liệu minh họa – không phải chương trình đào tạo chính thức' if result['source']=='DEMO' else 'Dữ liệu đã đồng bộ từ nguồn NEU.',styles['Normal']),Spacer(1,15)]
    for i,item in enumerate([next(x for x in result['items'] if x['id']==cid) for cid in result['ordering']],1):
        story.extend([Paragraph(f"{i}. {escape(item['name'])}",styles['Heading2']),
            Paragraph(escape(f"{item['code']} · {item['credits']} tín chỉ · Điểm phù hợp: {item['score']} · Học kỳ dự kiến {item['proposed_semester']}"),styles['Normal']),
            Paragraph(escape(item['reason']),styles['Normal']),
            Paragraph('Tiên quyết: '+escape(', '.join(item['prerequisites']) or 'Không có trong bộ dữ liệu'),styles['Normal'])])
    SimpleDocTemplate(output,title='Lộ trình học tập',author='NEU Learning Path',rightMargin=45,leftMargin=45,topMargin=40,bottomMargin=40).build(story)
    output.seek(0)
    return output
