from syllabus2ics.pdf_parser import extract_text_from_pdf
import reflex as rx
from syllabus2ics.syllabus_parsing import parse_syllabus


class State(rx.State):

    async def handle_upload(self, files: list[rx.UploadFile]):
        upload_data = await files[0].read()
        extracted_text = extract_text_from_pdf(upload_data)
        print(extracted_text)
        print("GOT A PDF")

        ics_string = parse_syllabus(extracted_text)
        return rx.download(data=ics_string.encode(), filename="my.ics")

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Syllabus to Calendar", size="9"),
            rx.text(
                "Automatically turn lectures/office hours in your syllabuys into calendar invites!"
            ),
            rx.upload(
                rx.text("Upload a PDF of your syllabus."),
                id="upload",
                multiple=False,
                accept={
                    "application/pdf": [".pdf"],
                },
                on_drop=State.handle_upload(rx.upload_files(upload_id="upload")),
                border=f"2px dotted",
                padding="3em",
                font_size="0.7em",
            ),
            # rx.html("<p>When does your class start?</p>"),
            # rx.html(
            #     '<input type="date" id="start" name="trip-start" value="2018-07-22" min="2018-01-01" max="2018-12-31" />'
            # ),
            align="center",
            spacing="7",
            font_size="1.7em",
        ),
        width="100vw",
        height="100vh",
    )


app = rx.App()
app.add_page(index)

