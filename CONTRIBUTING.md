# Contributing to Dimensio 📐

First off, thank you for considering contributing to Dimensio! It's people like you that make Dimensio such a great tool for the engineering community.

## 🚀 How Can I Contribute?

### Reporting Bugs
* **Check the Issue Tracker**: Someone might have already reported the issue.
* **Be Specific**: Include your OS version, Python version, and steps to reproduce the bug.
* **Screenshots/GIFs**: Visual aids are extremely helpful for UI bugs.

### Suggesting Enhancements
* **Open an Issue**: Explain why the feature would be useful and how it should work.
* **Sketch it Out**: If it's a UI change, a simple drawing or description goes a long way.

### Pull Requests
1. **Fork the repo** and create your branch from `main`.
2. **Setup your environment**: Follow the steps in the README.
3. **Follow the Architecture**: Ensure new features follow the established **Signal-based architectural pattern** using PySide6.
4. **Consistency**: Maintain the "Studio" aesthetic (Inter font, dark mode, vibrant accents).
5. **Update Documentation**: If you add a new feature or change a shortcut, update the README.

## 🏛️ Architectural Guidelines

Dimensio is built with high-performance desktop compositing in mind. When contributing code:
* **Avoid heavy operations on the UI thread**: Use Qt's signal/slot mechanism for asynchronous updates.
* **Modular Design**: Keep UI logic in `src/sidebar` and core geometry logic in dedicated managers.
* **State Persistence**: Ensure any new frame properties are correctly serialized in the `.dio` format.

---

*Happy Drafting!*
