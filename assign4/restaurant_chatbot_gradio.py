"""Gradio web app for the restaurant chatbot.

Run this file to open the chatbot in a browser.
"""

import gradio as gr

from restaurant_chatbot import process_message


def format_chat_line(sender: str, message: str) -> str:
    """Format one chat message."""

    return f"{sender}:\n{message}\n\n"


def add_message_to_chat(user_message, chat_history):
    """Add a user message and bot response to the chat history."""

    if chat_history is None:
        chat_history = ""

    if not user_message or not user_message.strip():
        return "", chat_history

    try:
        bot_answer = process_message(user_message)
    except Exception as error:
        bot_answer = (
            "Sorry, something went wrong while processing your request.\n"
            f"Error details: {error}"
        )

    chat_history += format_chat_line("You", user_message)
    chat_history += format_chat_line("Bot", bot_answer)

    return "", chat_history


def add_quick_message(user_message, chat_history):
    """Add a quick-button message and bot response to the chat history."""

    if chat_history is None:
        chat_history = ""

    try:
        bot_answer = process_message(user_message)
    except Exception as error:
        bot_answer = (
            "Sorry, something went wrong while processing your request.\n"
            f"Error details: {error}"
        )

    chat_history += format_chat_line("You", user_message)
    chat_history += format_chat_line("Bot", bot_answer)

    return chat_history


def quick_menu(chat_history):
    """Show the menu."""

    return add_quick_message("Show me the menu", chat_history)


def quick_hours(chat_history):
    """Show opening hours."""

    return add_quick_message("What are your opening hours?", chat_history)


def quick_reservation(chat_history):
    """Create an example reservation."""

    message = (
        "Book a table for 4 on 2026-08-05 at 19:30. "
        "My name is Shirel. Contact: 050-555-0142"
    )

    return add_quick_message(message, chat_history)


def fill_cancellation_example():
    """Fill the message box with a cancellation example, but do not send it automatically."""

    return "Cancel reservation ID "


def clear_chat():
    """Clear the chat history."""

    return ""


def main():
    """Launch the Gradio chatbot app."""

    css = """
    body {
        background: linear-gradient(135deg, #fff7ed, #ffe4e6, #fef3c7);
    }

    .main-container {
        max-width: 950px;
        margin: auto;
    }

    .title-box {
        text-align: center;
        padding: 25px;
        border-radius: 22px;
        background: linear-gradient(135deg, #fb7185, #f97316);
        color: white;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        margin-bottom: 20px;
    }

    .title-box h1 {
        font-size: 38px;
        margin-bottom: 8px;
    }

    .title-box p {
        font-size: 17px;
        margin: 0;
    }

    .info-card {
        background: white;
        color: black;
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        margin-bottom: 15px;
        text-align: center;
        font-size: 16px;
    }

    .chat-box textarea {
        background: #ffffff !important;
        color: #111827 !important;
        border-radius: 18px !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
    }

    .gradio-container {
        font-family: Arial, sans-serif;
    }

    button {
        border-radius: 14px !important;
        font-weight: bold !important;
    }
    """

    with gr.Blocks() as demo:

        with gr.Column(elem_classes="main-container"):

            gr.HTML(
                """
                <div class="title-box">
                    <h1>Sunset Bistro Chatbot</h1>
                    <p>Your friendly restaurant assistant for menu, opening hours, bookings, and cancellations.</p>
                </div>
                """
            )

            gr.HTML(
                """
                <div class="info-card">
                    Ask about the menu, opening hours, table reservations, or reservation cancellations.
                </div>
                """
            )

            chat_history = gr.Textbox(
                label="Restaurant Chat",
                value="",
                lines=18,
                interactive=False,
                elem_classes="chat-box",
            )

            with gr.Row():
                message_box = gr.Textbox(
                    placeholder="Type your message here...",
                    label="Your message",
                    scale=5,
                )

                send_button = gr.Button(
                    "Send",
                    variant="primary",
                    scale=1,
                )

            with gr.Row():
                menu_button = gr.Button("Show Menu")
                hours_button = gr.Button("Opening Hours")

            with gr.Row():
                reservation_button = gr.Button("Book Example")
                cancellation_button = gr.Button("Fill Cancel Message")
                clear_button = gr.Button("Clear Chat")

            gr.HTML(
                """
                <div class="info-card">
                    Example reservation format:<br>
                    <b style="color: black;">
                        Book a table for 4 on 2026-08-05 at 19:30. My name is Shirel. Contact: 050-555-0142
                    </b>
                </div>
                """
            )

            send_button.click(
                fn=add_message_to_chat,
                inputs=[message_box, chat_history],
                outputs=[message_box, chat_history],
            )

            message_box.submit(
                fn=add_message_to_chat,
                inputs=[message_box, chat_history],
                outputs=[message_box, chat_history],
            )

            menu_button.click(
                fn=quick_menu,
                inputs=[chat_history],
                outputs=[chat_history],
            )

            hours_button.click(
                fn=quick_hours,
                inputs=[chat_history],
                outputs=[chat_history],
            )

            reservation_button.click(
                fn=quick_reservation,
                inputs=[chat_history],
                outputs=[chat_history],
            )

            cancellation_button.click(
                fn=fill_cancellation_example,
                inputs=[],
                outputs=[message_box],
            )

            clear_button.click(
                fn=clear_chat,
                inputs=[],
                outputs=[chat_history],
            )

    demo.launch(
        theme=gr.themes.Soft(
            primary_hue="rose",
            secondary_hue="orange",
        ),
        css=css,
    )


if __name__ == "__main__":
    main()