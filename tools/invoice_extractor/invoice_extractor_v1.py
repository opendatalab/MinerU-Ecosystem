"""
MinerU 发票提取器
PDF 发票 → MinerU SDK 批量提取 JSON → LLM 结构化提取 → Excel
"""
import os
import sys

import json
from pathlib import Path
from dotenv import load_dotenv

from mineru import MinerU, FileParam
from openai import OpenAI
from openpyxl import Workbook

# -------- 加载环境变量 --------
load_dotenv()

MINERU_TOKEN = os.getenv("MINERU_TOKEN")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

EXTRACT_PROMPT = '你是一个发票信息提取器。以下是MinerU SDK从发票图片中提取的content_list。每个文本块格式：{"type": "text", "text": "发票号码：144000000000", ...} 或 {"type": "table", "table_body": "<table>...<td>价税合计(小写)</td><td>¥ 90000.00</td>...</table>"}。请找出：1)发票号码(以"发票号码："开头的text冒号后数字) 2)开票日期("开票日期："开头，转YYYY-MM-DD) 3)价税合计(表格中"价税合计(小写)"对应¥后面数字)。只返回JSON，不要任何解释或思考过程。格式：{"invoice_number":"","date":"","total":""}'


def parse_invoices(pdf_dir: str):
    """将目录下所有 PDF/图片通过 MinerU SDK 批量提取，解完一个 yield 一个"""
    # 支持 PDF 和常见图片格式
    files = []
    for ext in ["*.pdf", "*.jpg", "*.jpeg", "*.png", "*.bmp"]:
        files.extend(sorted(Path(pdf_dir).glob(ext)))
    if not files:
        print("No files found (supported: pdf, jpg, png, bmp)")
        return

    if not MINERU_TOKEN:
        print("Error: MINERU_TOKEN not set")
        return

    client = MinerU(MINERU_TOKEN)

    # extract_batch 支持的全局参数：
    #   model     - 模型版本: "vlm"(推荐) / "pipeline" / "html"，默认自动推断
    #   ocr       - 是否开启 OCR，默认 False
    #   formula   - 是否开启公式识别，默认 True
    #   table     - 是否开启表格识别，默认 True
    #   language  - 文档语言，默认 "ch"
    #   extra_formats - 额外导出格式: ["docx", "html", "latex"]
    #   timeout   - 轮询超时秒数，默认 1800
    #   file_params - 按文件覆盖参数，key 为文件路径，value 为 FileParam

    # FileParam 支持的字段：
    #   pages   - 页码范围，如 "1-5"
    #   ocr     - 覆盖全局 OCR 开关
    #   data_id - 自定义业务标识

    # 发票是扫描件/图片，需要开 OCR；通过 FileParam 按文件设置参数
    file_params = {str(f): FileParam(ocr=True) for f in files}
    for result in client.extract_batch(
        [str(f) for f in files],
        table=True,         # 发票中的金额在表格里，确保开启
        file_params=file_params,
    ):
        print(f"  Parsed: {result.filename}")
        yield {"filename": result.filename, "content": result.content_list}
    client.close()


def extract_fields(invoice: dict, llm: OpenAI) -> dict:
    """将单张发票的 content_list 喂给 LLM，提取发票号码/日期/金额"""
    content_str = json.dumps(invoice["content"], ensure_ascii=False)
    resp = llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": EXTRACT_PROMPT + content_str}],
        temperature=0
    )
    raw = resp.choices[0].message.content.strip()
    try:
        fields = json.loads(raw)
    except json.JSONDecodeError:
        fields = {"invoice_number": "PARSE_ERROR", "date": "", "total": ""}
    fields["filename"] = invoice["filename"]
    print(f"  Extracted: {invoice['filename']}")
    return fields


def write_excel(data: list[dict], output: str = "发票汇总.xlsx"):
    """将提取结果写入 Excel"""
    wb = Workbook()
    ws = wb.active
    ws.append(["文件名", "发票号码", "开票日期", "价税合计"])
    for row in data:
        ws.append([
            row.get("filename"),
            row.get("invoice_number"),
            row.get("date"),
            row.get("total")
        ])
    wb.save(output)
    print(f"已保存: {output}")


def main():
    if not LLM_API_KEY:
        print("Error: LLM_API_KEY not set")
        sys.exit(1)

    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else "./invoices"
    llm = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    results = []
    for invoice in parse_invoices(pdf_dir):
        results.append(extract_fields(invoice, llm))

    write_excel(results)


if __name__ == "__main__":
    main()
