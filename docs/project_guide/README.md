# Project guide

`Stepwise_Confidence_Project_Guide.pdf` is the 20-page English walkthrough.
`Stepwise_Confidence_Project_Guide.md` is the editable companion with the same content.
`snapshot.json` freezes the data, baseline metrics and dated worker status used in the guide.
`verification.json` records content/layout checks and the PDF hash.

Rebuild the frozen guide on this Mac:

```bash
python3 docs/project_guide/build_guide.py
```

The builder uses the system Python's existing ReportLab installation and macOS Arial fonts.
PyMuPDF was used separately for text/bounds checks and rendered visual inspection.
Generating this guide does not modify or restart the MCS/GCN experiment.
The guide was saved locally and in Downloads; it was not pushed to GitHub.
