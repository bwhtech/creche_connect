### CrecheConnect

Audience-targeted threads for field programmes

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app creche_connect
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/creche_connect
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### Interface translations

The language switcher uses the Frappe translation catalog in `creche_connect/locale`.
Add full interface strings there when introducing labels or messages. Thread titles,
post and reply bodies, and poll options display as written in every language and
do not require catalog entries.

### License

mit
