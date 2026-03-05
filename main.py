from cli_main import main as cli_main
from splashkit_launcher import launch_application


def choose_mode_cli():
    while True:
        print("\nChoose mode:")
        print("1. CLI (Terminal)")
        print("2. GUI (SplashKit)")
        choice = input("Choice (1/2): ").strip()

        if choice in ("1", "2"):
            return choice
        else:
            print("Invalid choice. Please enter 1 or 2.")


def run_cli():
    cli_main()


def run_gui():
    launch_application()


def main():
    choice = choose_mode_cli()

    if choice == "1":
        run_cli()
    elif choice == "2":
        try:
            run_gui()
        except Exception as e:
            print(f"\n⚠ GUI failed: {e}")
            print("Falling back to CLI...\n")
            run_cli()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
