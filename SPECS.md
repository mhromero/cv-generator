# CV Generator

## Goal

Generate CV as PDF using data from a markdown CV definition.

## Procedure

* Parse Markdown into the different CV sections
* Generate an intermediate Latex representation according to a given CV template (default: moderncv)
* Render the Latex to PDF

## Example

In a local `./example` directory (kept out of version control):

cv.md -> CV data
cv.tex -> latex intermediate template
cv.pdf -> final PDF

## Technical Requirements

* Python 3
* uv dependencies management
* Latex for presentation
* PDF final CV

## Deliverable

* Python based project
* README.md with install and usage instructions


## Definition of Done

Use the provided example markdown data and generate the PDF.
Verify that the latex template is identical to the provided one and the user confirms that the PDF is acceptable.

## Agent Direction

* Keep the code simple but don't skip anything essential
* Add comments to the relevant functions and code blocks; keep them clear and concise
* Guide the user through the installation of required software (example: python 3 virtual env or the latex distribution)
* If possible, compare the PDFs yourself to verify that the job is done; otherwise pause and ask the user to check the PDF
