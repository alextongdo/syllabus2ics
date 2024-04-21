from syllabus2ics.pdf_parser import extract_text_from_pdf
import reflex as rx
from syllabus2ics.syllabus_parsing import parse_syllabus


class State(rx.State):

    show_progress: bool = False
    message: str = "Upload a PDF of your syllabus."
    
    async def handle_upload(self, files: list[rx.UploadFile]):
        self.show_progress = True
        self.message = "Loading..."
        yield
        upload_data = await files[0].read()
        extracted_text = extract_text_from_pdf(upload_data)
        print(extracted_text)
        print("GOT A PDF")
        ics_string = parse_syllabus(extracted_text)
        self.show_progress = False
        self.message = "Upload a PDF of your syllabus."
        yield rx.download(data=ics_string.encode(), filename="my.ics")

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading('\U0001F4DA Syllabus to Calendar \U0001F4C5', size="9"),
            rx.text(
                "Automatically turn lectures/office hours in your syllabus into calendar invites!"
            ),
            rx.vstack(
                rx.upload(
                    rx.text(State.message, align="center"),
                    id="upload",
                    multiple=False,
                    accept={
                        "application/pdf": [".pdf"],
                    },
                    on_drop=State.handle_upload(rx.upload_files(upload_id="upload")),
                    border=f"2px dotted",
                    padding="3em",
                    width="100%",
                    font_size="0.7em",
                ),
                rx.cond(
                    State.show_progress,
                    rx.chakra.progress(is_indeterminate=True, width="100%"),
                ),
                width="50%",
                spacing="4",
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

