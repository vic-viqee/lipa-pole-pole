# Chama Management System

#### Video Demo: https://youtu.be/8T_FWtOsSHA

#### Description:

## What is a Chama?

A **Chama** is an informal savings and investment group that is deeply embedded in Kenyan culture and society. The word itself comes from the Swahili word meaning "group" or "association." Chamas bring together friends, family members, colleagues, or neighbours who pool their money together to save, invest, and support one another financially. They operate on a foundation of trust, discipline, and collective accountability — values that formal financial institutions often fail to provide for everyday Kenyans.

The Chama Management System is a command-line Python application designed to digitise and streamline the management of two of the most popular types of Chamas in Kenya: the **Merry-Go-Round** and **Table Banking**. The goal of this project is to replace the handwritten ledgers, scattered WhatsApp messages, and mental arithmetic that most Chamas still rely on today, and replace them with a clean, organised, and reliable record-keeping system.

---

## How the System Works

When the program is launched by running `python project.py`, it first ensures all the necessary CSV data files exist in a `data/` folder (creating them automatically if they don't). It then presents the user with a main menu from which they can navigate into five core modules: Member Management, Merry-Go-Round, Table Banking, Fines & Discipline, and Reports. Each module has its own sub-menu, and the user navigates by typing a number and pressing Enter. All data entered is immediately saved to the relevant CSV file so nothing is lost between sessions.

---

## Project Files

### `project.py`

This is the heart of the application. It contains the `main()` function as well as every other function the system needs. The file is organised into clearly separated sections:

**Initialisation & Utilities** — The `initialise_files()` function checks for the existence of the five CSV data files and creates them with the correct headers if they are missing. Helper functions like `read_csv()`, `write_csv()`, `append_csv()`, and `generate_id()` handle all CSV input and output throughout the app, keeping the data layer clean and consistent.

**Core Functions (CS50P Required)** — These four functions are the most important in the project and are the ones covered by the test suite:

- `calculate_fine(fine_type, amount_owed)` takes a fine type string and an optional amount and returns the correct fine in KES. Late coming is a fixed 50 KES, absenteeism is a fixed 100 KES, and late contributions are charged at 5% of the amount owed. The function raises a `ValueError` for unrecognised fine types or negative amounts.

- `calculate_loan_interest(principal, rate_percent, months)` uses the simple interest formula to return the total amount a borrower must repay. It validates that all three arguments are positive numbers and raises a `ValueError` otherwise. Simple interest was chosen over compound interest deliberately — most Kenyan Table Banking Chamas use simple interest because it is transparent and easy for all members to verify without a calculator.

- `validate_member(member_id, members_list)` checks whether a given member ID exists in a list of member dictionaries and returns `True` or `False`. This function is called throughout the app before any transaction is recorded, preventing orphaned records for non-existent members.

- `calculate_merry_go_round_payout(members_list, contribution_amount)` multiplies the number of members by the fixed contribution to return the total pot for that cycle. It raises a `ValueError` if the members list is empty or if the contribution amount is not positive.

**Member Management** — `add_member()` registers a new member and assigns them a sequential ID (M001, M002, etc.). `view_members()` prints a formatted table of all members. `remove_member()` deletes a member record by ID.

**Merry-Go-Round Module** — `setup_mgr_rotation()` reads all Merry-Go-Round members and assigns them a numbered position in the rotation queue. `record_mgr_contribution()` logs each member's payment into the contributions CSV. `assign_mgr_payout()` marks a member as having received their turn and records the date. `view_mgr_rotation()` displays the full rotation table with names, positions, and payout status.

**Table Banking Module** — `record_share_contribution()` logs a member's share deposit. `apply_for_loan()` issues a loan after calculating the total repayable amount and saves the full loan record. `repay_loan()` updates the amount repaid on an active loan and automatically marks it as paid when the balance is cleared. If the treasurer indicates the repayment is late, the system automatically triggers `issue_fine()` with the `late_contribution` type. `view_loan_book()` displays all loans with their current balance and status.

**Fines & Discipline Module** — `issue_fine()` calculates the appropriate fine using `calculate_fine()` and saves it to the fines ledger. `mark_fine_paid()` updates a fine's paid status. `view_fines()` displays the full fines ledger with member names and payment status.

**Reports Module** — `generate_report()` accepts a report type string (`"all"`, `"members"`, `"loans"`, `"fines"`, or `"mgr"`) and prints a clean summary to the terminal. It aggregates data across all CSVs to show totals like members by type, total money lent, interest earned, and fines collected.

**CLI Menus** — Five menu functions (`menu_member_management`, `menu_merry_go_round`, `menu_table_banking`, `menu_fines`, `menu_reports`) each run a `while True` loop that displays options and routes the user's input to the correct function. The `main()` function ties them all together under the top-level menu.

---

### `test_project.py`

This file contains the full pytest test suite, organised into four test classes — one for each of the four core functions. In total there are **48 individual test cases** covering normal operation, edge cases, and error handling.

`TestCalculateFine` verifies correct fine amounts for all three fine types, confirms that fixed fines ignore the `amount_owed` argument, checks that the function is case-insensitive, and confirms that `ValueError` is raised for invalid inputs.

`TestCalculateLoanInterest` tests interest calculations at various principal amounts, rates, and durations. It also confirms that the result is always greater than the principal, that the return value is rounded to two decimal places, and that all three invalid-input scenarios (zero or negative values) correctly raise `ValueError`.

`TestValidateMember` uses a pytest fixture to provide a reusable sample members list. It verifies that known IDs return `True`, unknown IDs return `False`, that the function is case-sensitive (so `m001` does not match `M001`), and that an empty list always returns `False`.

`TestCalculateMerryGoRoundPayout` tests payouts for groups of different sizes, confirms that a larger group produces a larger pot, and verifies that `ValueError` is raised for an empty member list, a zero contribution, or a negative contribution.

---

### `requirements.txt`

Lists the two external libraries the project depends on: `tabulate` for rendering CSV data as clean terminal tables, and `pytest` for running the test suite. All other modules used (`csv`, `os`, `sys`, `datetime`) are part of Python's standard library.

---

### `data/` folder

This folder is created automatically on first run and contains five CSV files that serve as the system's database:

- `members.csv` — stores member ID, name, phone number, Chama type, number of shares, and join date.
- `contributions.csv` — records every contribution with a type field distinguishing Merry-Go-Round from Table Banking deposits.
- `loans.csv` — stores the full lifecycle of each loan: principal, rate, months, total repayable, amount repaid, and status.
- `fines.csv` — logs each fine with its type, amount, paid status, and date.
- `merry_go_round.csv` — tracks the rotation queue, recording each member's position and whether they have received their payout.

CSV was chosen over a database like SQLite deliberately. CSV files are human-readable and can be opened directly in Microsoft Excel or Google Sheets, which is exactly the kind of tool a Chama treasurer is likely to already be familiar with. A member can verify their own record by simply opening the file — no technical knowledge required. This transparency is important in a trust-based financial group.

---

## How to Run

**1. Clone or download the project files.**

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Run the application:**
```bash
python project.py
```

**4. Run the test suite:**
```bash
pytest test_project.py -v
```

---

## Design Decisions

**Why simple interest?** Compound interest would have been mathematically more sophisticated, but simple interest is what real Kenyan Chamas use. The priority was authenticity to how these groups actually operate, not technical complexity.

**Why CSV instead of SQLite?** While SQLite would have been more robust for a production app, CSV files make the data immediately accessible to the treasurer without any software beyond a spreadsheet application. The transparency of plain-text files aligns with the trust-first culture of Chamas.

**Why a CLI over a web app?** A CLI keeps the project focused on Python fundamentals as required by CS50P, avoids the overhead of HTML/CSS/JavaScript, and can run on any computer — including low-end machines — without a browser or internet connection.

**Why organise tests into classes?** Grouping tests into `TestCalculateFine`, `TestCalculateLoanInterest`, etc. makes the test output easier to read and allows pytest fixtures (like the sample members list) to be scoped cleanly to the relevant group of tests.

---

## Acknowledgements

This project was built as the final project for **CS50's Introduction to Programming with Python (CS50P)** offered by Harvard University via edX. The domain knowledge comes from firsthand familiarity with how Chamas operate across Kenya.