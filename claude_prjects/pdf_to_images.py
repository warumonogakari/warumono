#!/usr/bin/env python3
"""
PDF to Images Converter
PDFファイルを各ページの画像ファイルに変換するスクリプト
"""

from pdf2image import convert_from_path
import os
import sys

def pdf_to_images(pdf_path, output_dir=None, dpi=200):
    """
    PDFを画像に変換

    Args:
        pdf_path: PDFファイルのパス
        output_dir: 出力先ディレクトリ（省略時はPDFと同名のフォルダ）
        dpi: 解像度（デフォルト150）
    """
    if output_dir is None:
        output_dir = os.path.splitext(pdf_path)[0]

    os.makedirs(output_dir, exist_ok=True)

    print(f"Converting: {pdf_path}")
    print(f"Output dir: {output_dir}")
    print("-" * 40)

    images = convert_from_path(pdf_path, dpi=dpi)

    for i, image in enumerate(images, 1):
        image_path = os.path.join(output_dir, f"page_{i:03d}.png")
        image.save(image_path, "PNG")
        print(f"[{i}/{len(images)}] Saved: {image_path}")

    print("-" * 40)
    print(f"Done! {len(images)} pages converted.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_images.py <pdf_path>")
        sys.exit(1)

    pdf_to_images(sys.argv[1])
