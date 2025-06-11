from datetime import datetime
import io
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


class IngredientPDFExporter:
    def __init__(self):
        self._buffer = io.BytesIO()
        self._pdf = canvas.Canvas(self._buffer)

        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        self._pdf.setFont('DejaVuSans', 12)

        self._pdf.drawString(100, 800, 'Список покупок')
        self._pdf.drawString(400, 800, datetime.now().strftime('%d.%m.%Y'))
        self._current_y = 780

    def finalize(self):
        self._pdf.save()
        self._buffer.seek(0)
        return self._buffer

    def add_items(self, ingredients):
        for idx, item in enumerate(ingredients, start=1):
            self._pdf.drawString(
                100,
                self._current_y,
                f"{idx}. {item['name'].capitalize()} "
                f"- {item['total_amount']}{item['measurement_unit']}"
            )
            self._current_y -= 20
