"""
SplashKit Launcher - Entry point for the Business Strategy Simulator.
"""

from splashkit import *
from gui_main import BusinessSimulatorGUI


def show_splash_screen():
    window = open_window("Business Strategy Simulator", 800, 600)

    bg_color = rgb_color(44, 62, 80)
    text_color = rgb_color(236, 240, 241)
    accent_color = rgb_color(52, 152, 219)

    dots = ""
    frame_count = 0
    total_frames = 90

    load_font("main_font", "Arial.ttf")

    while frame_count < total_frames and not quit_requested():
        process_events()
        clear_screen(bg_color)

        draw_text(
            "Business Strategy Simulator",
            text_color,
            font_named("main_font"),
            40,
            150,
            150,
        )
        draw_text(
            "AI-Powered Decision Support System",
            accent_color,
            font_named("main_font"),
            20,
            200,
            220,
        )

        features = [
            "✓ 12-Month Business Simulation",
            "✓ Monte Carlo Risk Analysis",
            "✓ Root Cause Diagnosis",
            "✓ Interactive Recommendations",
        ]

        y_offset = 300
        for feature in features:
            draw_text(feature, text_color, font_named("main_font"), 16, 250, y_offset)
            y_offset += 30

        if frame_count % 10 == 0:
            dots = "." * ((frame_count // 10) % 4)

        draw_text(f"Loading{dots}", accent_color, font_named("main_font"), 18, 330, 500)

        progress = frame_count / total_frames
        fill_rectangle(rgb_color(52, 73, 94), 200, 530, 400, 20)
        fill_rectangle(accent_color, 200, 530, 400 * progress, 20)
        draw_rectangle(text_color, 200, 530, 400, 20)

        draw_text(
            "Powered by SplashKit & Python",
            rgb_color(149, 165, 166),
            font_named("main_font"),
            12,
            280,
            570,
        )

        refresh_screen()
        delay(33)
        frame_count += 1

    close_window(window)


def show_closing_screen():
    window = open_window("Business Strategy Simulator - Closing", 800, 600)

    bg_color = rgb_color(44, 62, 80)
    text_color = rgb_color(236, 240, 241)
    accent_color = rgb_color(52, 152, 219)

    dots = ""
    frame_count = 0
    total_frames = 60

    try:
        load_font("main_font", "Arial.ttf")
    except:
        pass

    while frame_count < total_frames:
        process_events()
        clear_screen(bg_color)

        glow = 0.7 + 0.3 * ((frame_count % 20) / 20)
        draw_text(
            "Closing Business Strategy Simulator",
            hsb_color(0.55, 0.3, glow),
            font_named("main_font"),
            40,
            80,
            150,
        )
        draw_text(
            "Saving your session and cleaning up...",
            accent_color,
            font_named("main_font"),
            20,
            200,
            220,
        )

        progress = frame_count / total_frames
        fill_rectangle(rgb_color(52, 73, 94), 200, 530, 400, 20)
        fill_rectangle(accent_color, 200, 530, 400 * progress, 20)
        draw_rectangle(text_color, 200, 530, 400, 20)

        if frame_count % 10 == 0:
            dots = "." * ((frame_count // 10) % 4)
        draw_text(f"Closing{dots}", accent_color, font_named("main_font"), 18, 330, 500)

        draw_text(
            "Thank you for using Business Strategy Simulator",
            rgb_color(149, 165, 166),
            font_named("main_font"),
            12,
            220,
            570,
        )

        refresh_screen()
        delay(33)
        frame_count += 1

    close_window(window)


def launch_application():
    """
    Main launcher function.
    """
    print("=" * 60)
    print("BUSINESS STRATEGY SIMULATOR")
    print("=" * 60)
    print("\n[1/2] Initializing SplashKit splash screen...")

    show_splash_screen()
    app = BusinessSimulatorGUI()

    def on_close():
        app.root.withdraw()
        show_closing_screen()
        app.root.destroy()

    app.set_exit_handler(on_close)
    app.root.protocol("WM_DELETE_WINDOW", on_close)
    app.run()


if __name__ == "__main__":
    launch_application()
