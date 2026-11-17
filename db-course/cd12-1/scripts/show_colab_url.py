"""Show the linked Colab notebook address on the CD12-1 practice slide."""
import argparse
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt


def update(source, output):
    deck = Presentation(source)
    candidates = [s for s in deck.slides if s.shapes.title is not None
                  and s.shapes.title.text.startswith("Colab 실습 | 쇼핑몰 DB")]
    if len(candidates) != 1:
        raise ValueError("Expected one CD12-1 shopping lab slide.")
    slide = candidates[0]
    button, = [sh for sh in slide.shapes if sh.has_text_frame
               and sh.text == "Colab · DB 생성부터 실행"]
    url = button.click_action.hyperlink.address.split("#", 1)[0]
    if not url.startswith("https://colab.research.google.com/drive/"):
        raise ValueError("The practice button must link to Colab.")
    lead, = [sh for sh in slide.shapes if sh.has_text_frame
             and sh.text.startswith("아래 링크에서 코드 셀을")]
    lead.height = Inches(0.39)
    label = slide.shapes.add_textbox(Inches(0.98), Inches(1.94), Inches(11.45), Inches(0.34))
    frame = label.text_frame
    frame.margin_top = Pt(0)
    frame.margin_bottom = Pt(0)
    paragraph = frame.paragraphs[0]
    title = paragraph.add_run()
    title.text = "실습 노트북  "
    link = paragraph.add_run()
    link.text = url
    link.hyperlink.address = url
    for run in (title, link):
        run.font.name = "맑은 고딕"
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor.from_string("104982")
    title.font.bold = True
    link.font.underline = True
    deck.save(output)

    result = Presentation(output)
    target, = [s for s in result.slides if s.slide_id == slide.slide_id]
    visible, = [sh for sh in target.shapes if sh.has_text_frame and sh.text == label.text]
    assert visible.text_frame.paragraphs[0].runs[-1].hyperlink.address == url
    assert len(result.slides) == len(deck.slides)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("Use separate source and output paths.")
    update(args.source, args.output)
