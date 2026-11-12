from dataclasses import dataclass
from drafter import *
from bakery import assert_equal

set_website_title("Corgi Cafe")
set_site_information(
    author="Natalie Pesarchick",
    description="A christmas list organizing website",
    sources="Thanks to the Drafter docs and my study group.",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/natpes/christmas-list"]
)
hide_debug_information()
set_website_framed(False)

@dataclass
class Gift:
    name: str
    price: float
    is_bought: bool

@dataclass
class Person:
    name: str
    gifts: list[Gift]
    limit: float

@dataclass
class State:
    budget: float
    total_spent: float
    recipients: list[Person]
    per_person_limit: float

@route
def index(state: State) -> Page:
    """
    Show the home page with the budget, planned and spent totals,
    money left, and a warning if the plan is over budget.

    Args:
        state (State): the current app state

    Returns:
        Page: the Gift Tracker home page
    """
    planned = total_planned(state.recipients)
    content = [
        Header("Gift Tracker"),
        "Total budget: $" + str(state.budget),
        "Planned (all gifts): $" + str(planned),
        "Spent so far (bought): $" + str(state.total_spent),
        "Money left: $" + str(state.budget - planned),
        "Set your overall budget:",
        TextBox("new_budget", str(state.budget)),
        Button("Save Budget", save_budget),
        "Default limit per person: $" + str(state.per_person_limit),
        "Set default limit per person:",
        TextBox("new_limit", str(state.per_person_limit)),
        Button("Save Limit", save_limit),
        Button("View People!", view_people)
    ]
    if planned > state.budget:
        content.append("Warning: over budget by $" + str(planned - state.budget))
    return Page(state, content)

@route
def save_budget(state: State, new_budget: str) -> Page:
    """
    Save the overall budget typed by the user.

    Args:
        state (State): the current app state
        new_budget (str): the budget the user typed in

    Returns:
        Page: the home page with the updated budget
    """
    state.budget = float(new_budget)
    return index(state)

@route
def save_limit(state: State, new_limit: str) -> Page:
    """
    Save the default per-person limit typed by the user.

    Args:
        state (State): the current app state
        new_limit (str): the limit the user typed in

    Returns:
        Page: the home page with the updated default limit
    """
    state.per_person_limit = float(new_limit)
    return index(state)

@route
def add_reciprient(state: State) -> Page:
    """
    Show the form for adding a new recipient and their limit.

    Args:
        state (State): the current app state

    Returns:
        Page: the Add Recipient form
    """
    return Page(state, [
        Header("Add Recipient"),
        "Name:",
        TextBox("name"),
        "Limit (0 means no limit):",
        TextBox("limit", str(state.per_person_limit)),
        Button("Save", save_reciprient),
        Button("Cancel", view_people)
    ])

@route
def save_reciprient(state: State, name: str, limit: float) -> Page:
    """
    Add a new person with no gifts to the list of recipients.

    Args:
        state (State): the current app state
        name (str): the new person's name
        limit (float): the new person's spending limit (0 means none)

    Returns:
        Page: the people list including the new person
    """
    state.recipients.append(Person(name, [], limit))
    return view_people(state)

@route
def view_people(state: State) -> Page:
    """
    Show a button for every recipient, plus buttons to add a
    recipient or go back to the home page.

    Args:
        state (State): the current app state

    Returns:
        Page: the people list page
    """
    content = [Header("People")]
    for person in state.recipients:
        content.append(Button(person.name, view_person, [Argument("person_name", person.name)]))
    content.append(Button("Add Recipient", add_reciprient))
    content.append(Button("Back", index))
    return Page(state, content)

@route
def view_person(state: State, person_name: str) -> Page:
    """
    Show one person's page: their limit, their gifts with a bought
    checkbox mark, and buttons to toggle gifts, add a gift, or go back.

    Args:
        state (State): the current app state
        person_name (str): the name of the person to display

    Returns:
        Page: the person's gift page, or the people list if no one
        matches person_name
    """
    # Find the person whose name matches the button that was clicked
    for person in state.recipients:
        if person.name == person_name:
            content = [Header(person.name + "'s Gifts")]
            content.append("Limit for " + person.name + ": $" + str(person.limit))
            # One line and one toggle button per gift
            for gift in person.gifts:
                mark = "[x] " if gift.is_bought else "[ ] "
                content.append(mark + gift.name + ": $" + str(gift.price))
                content.append(Button("Toggle bought", toggle_bought,
                                      [Argument("person_name", person.name),
                                       Argument("gift_name", gift.name)]))
            content.append(Button("Add Gift", add_gift, [Argument("person_name", person.name)]))
            content.append(Button("Back", view_people))
            return Page(state, content)
    # Fallback: no matching person was found
    return view_people(state)

@route
def toggle_bought(state: State, person_name: str, gift_name: str) -> Page:
    """
    Flip a gift between bought and not bought, then update the
    total spent.

    Args:
        state (State): the current app state
        person_name (str): the person the gift belongs to
        gift_name (str): the gift to toggle

    Returns:
        Page: the person's gift page with the updated checklist
    """
    for person in state.recipients:
        if person.name == person_name:
            for gift in person.gifts:
                if gift.name == gift_name:
                    gift.is_bought = not gift.is_bought
    state.total_spent = total_all(state.recipients)
    return view_person(state, person_name)

@route
def add_gift(state: State, person_name: str) -> Page:
    """
    Show the form for adding a gift for one person.

    Args:
        state (State): the current app state
        person_name (str): the person receiving the gift

    Returns:
        Page: the Add Gift form
    """
    return Page(state, [
        Header("Add Gift for " + person_name),
        "Gift Name:",
        TextBox("name"),
        "Price:",
        TextBox("price"),
        Button("Save", save_gift, [Argument("person_name", person_name)]),
        Button("Cancel", view_person, [Argument("person_name", person_name)])
    ])

@route
def save_gift(state: State, name: str, price: float, person_name: str) -> Page:
    """
    Check a new gift against the person's limit and the overall budget
    before adding it. If either would be exceeded, show a warning page
    that lets the user add the gift anyway or cancel.

    Args:
        state (State): the current app state
        name (str): the name of the new gift
        price (float): the price of the new gift
        person_name (str): the name of the person receiving the gift

    Returns:
        Page: a warning page if a limit would be passed, otherwise the
        result of confirm_gift (the person's updated gift page)
    """
    # Check 1: the person's own limit (0 means no limit)
    for person in state.recipients:
        if person.name == person_name:
            if person.limit > 0 and person_planned(person) + price > person.limit:
                return Page(state, [
                    Header("Over Person Limit"),
                    "Adding " + name + " ($" + str(price) + ") puts " + person_name +
                    " over their $" + str(person.limit) + " limit.",
                    Button("Add Anyway", confirm_gift, [Argument("name", name),
                                                        Argument("price", price),
                                                        Argument("person_name", person_name)]),
                    Button("Cancel", view_person, [Argument("person_name", person_name)])
                ])
    # Check 2: the overall budget
    if total_planned(state.recipients) + price > state.budget:
        return Page(state, [
            Header("Over Budget Warning"),
            "Adding " + name + " ($" + str(price) + ") will put you over your budget of $" + str(state.budget) + ".",
            Button("Add Anyway", confirm_gift, [Argument("name", name),
                                                Argument("price", price),
                                                Argument("person_name", person_name)]),
            Button("Cancel", view_person, [Argument("person_name", person_name)])
        ])
    # No limits passed, so add the gift
    return confirm_gift(state, name, price, person_name)

@route
def confirm_gift(state: State, name: str, price: float, person_name: str) -> Page:
    """
    Add a gift to a person's list without any limit checks, then
    update the total spent.

    Args:
        state (State): the current app state
        name (str): the gift's name
        price (float): the gift's price
        person_name (str): the person receiving the gift

    Returns:
        Page: the person's gift page including the new gift
    """
    for person in state.recipients:
        if person.name == person_name:
            person.gifts.append(Gift(name, price, False))
    state.total_spent = total_all(state.recipients)
    return view_person(state, person_name)

def person_planned(person: Person) -> float:
    """
    Add up the prices of all of one person's gifts, bought or not.

    Args:
        person (Person): the person whose gifts to total

    Returns:
        float: the total price of the person's gifts
    """
    total = 0.0
    for gift in person.gifts:
        total = total + gift.price
    return total

def total_planned(people: list[Person]) -> float:
    """
    Add up the prices of every gift for every person, bought or not.

    Args:
        people (list[Person]): all of the recipients

    Returns:
        float: the total planned cost
    """
    total = 0.0
    for person in people:
        total = total + person_planned(person)
    return total

def total_gifts(gifts: list[Gift]) -> float:
    """
    Add up the prices of only the gifts marked as bought.

    Args:
        gifts (list[Gift]): the gifts to total

    Returns:
        float: the total cost of the bought gifts
    """
    total = 0.0
    for gift in gifts:
        if gift.is_bought:
            total = total + gift.price
    return total

def total_all(people: list[Person]) -> float:
    """
    Add up the prices of all bought gifts across every person.

    Args:
        people (list[Person]): all of the recipients

    Returns:
        float: the total amount spent so far
    """
    total = 0.0
    for person in people:
        total = total + total_gifts(person.gifts)
    return total


# ======================= UNIT TESTS =======================

# ---------- helper functions ----------
assert_equal(person_planned(Person("Ann", [], 0.0)), 0.0)
assert_equal(person_planned(Person("Ann", [Gift("Book", 10.0, False), Gift("Pen", 5.0, True)], 0.0)), 15.0)

assert_equal(total_planned([]), 0.0)
assert_equal(total_planned([Person("Ann", [Gift("Book", 10.0, False)], 0.0),
                            Person("Bo", [Gift("Pen", 5.0, True)], 0.0)]), 15.0)

# total_gifts / total_all only count BOUGHT gifts
assert_equal(total_gifts([Gift("Book", 10.0, False), Gift("Pen", 5.0, True)]), 5.0)
assert_equal(total_gifts([]), 0.0)
assert_equal(total_all([Person("Ann", [Gift("Book", 10.0, True)], 0.0),
                        Person("Bo", [Gift("Pen", 5.0, False)], 0.0)]), 10.0)

# ---------- index ----------
assert_equal(
    index(State(100.0, 0.0, [], 0.0)),
    Page(State(100.0, 0.0, [], 0.0), [
        Header("Gift Tracker"),
        "Total budget: $100.0",
        "Planned (all gifts): $0.0",
        "Spent so far (bought): $0.0",
        "Money left: $100.0",
        "Set your overall budget:",
        TextBox("new_budget", "100.0"),
        Button("Save Budget", save_budget),
        "Default limit per person: $0.0",
        "Set default limit per person:",
        TextBox("new_limit", "0.0"),
        Button("Save Limit", save_limit),
        Button("View People!", view_people)
    ]))

# over budget: warning line is added
over = State(50.0, 0.0, [Person("Ann", [Gift("Book", 60.0, False)], 0.0)], 0.0)
assert_equal(
    index(over),
    Page(over, [
        Header("Gift Tracker"),
        "Total budget: $50.0",
        "Planned (all gifts): $60.0",
        "Spent so far (bought): $0.0",
        "Money left: $-10.0",
        "Set your overall budget:",
        TextBox("new_budget", "50.0"),
        Button("Save Budget", save_budget),
        "Default limit per person: $0.0",
        "Set default limit per person:",
        TextBox("new_limit", "0.0"),
        Button("Save Limit", save_limit),
        Button("View People!", view_people),
        "Warning: over budget by $10.0"
    ]))

# ---------- save_budget / save_limit ----------
assert_equal(save_budget(State(0.0, 0.0, [], 0.0), "75.5"),
             index(State(75.5, 0.0, [], 0.0)))
assert_equal(save_limit(State(0.0, 0.0, [], 0.0), "20.0"),
             index(State(0.0, 0.0, [], 20.0)))

# ---------- add_reciprient ----------
assert_equal(
    add_reciprient(State(0.0, 0.0, [], 25.0)),
    Page(State(0.0, 0.0, [], 25.0), [
        Header("Add Recipient"),
        "Name:",
        TextBox("name"),
        "Limit (0 means no limit):",
        TextBox("limit", "25.0"),
        Button("Save", save_reciprient),
        Button("Cancel", view_people)
    ]))

# ---------- save_reciprient ----------
assert_equal(save_reciprient(State(0.0, 0.0, [], 0.0), "Colin", 20.0),
             view_people(State(0.0, 0.0, [Person("Colin", [], 20.0)], 0.0)))
# adds to the end of an existing list
assert_equal(save_reciprient(State(0.0, 0.0, [Person("Ann", [], 0.0)], 0.0), "Bo", 5.0),
             view_people(State(0.0, 0.0, [Person("Ann", [], 0.0), Person("Bo", [], 5.0)], 0.0)))

# ---------- view_people ----------
assert_equal(
    view_people(State(0.0, 0.0, [], 0.0)),
    Page(State(0.0, 0.0, [], 0.0), [
        Header("People"),
        Button("Add Recipient", add_reciprient),
        Button("Back", index)
    ]))
two = State(0.0, 0.0, [Person("Ann", [], 0.0), Person("Bo", [], 0.0)], 0.0)
assert_equal(
    view_people(two),
    Page(two, [
        Header("People"),
        Button("Ann", view_person, [Argument("person_name", "Ann")]),
        Button("Bo", view_person, [Argument("person_name", "Bo")]),
        Button("Add Recipient", add_reciprient),
        Button("Back", index)
    ]))

# ---------- view_person ----------
s = State(0.0, 0.0, [Person("Colin", [Gift("Book", 10.0, True), Gift("Pen", 5.0, False)], 20.0)], 0.0)
assert_equal(
    view_person(s, "Colin"),
    Page(s, [
        Header("Colin's Gifts"),
        "Limit for Colin: $20.0",
        "[x] Book: $10.0",
        Button("Toggle bought", toggle_bought, [Argument("person_name", "Colin"),
                                                Argument("gift_name", "Book")]),
        "[ ] Pen: $5.0",
        Button("Toggle bought", toggle_bought, [Argument("person_name", "Colin"),
                                                Argument("gift_name", "Pen")]),
        Button("Add Gift", add_gift, [Argument("person_name", "Colin")]),
        Button("Back", view_people)
    ]))
# person with no gifts
s = State(0.0, 0.0, [Person("Ann", [], 0.0)], 0.0)
assert_equal(
    view_person(s, "Ann"),
    Page(s, [
        Header("Ann's Gifts"),
        "Limit for Ann: $0.0",
        Button("Add Gift", add_gift, [Argument("person_name", "Ann")]),
        Button("Back", view_people)
    ]))
# name not found falls back to the people list
assert_equal(view_person(State(0.0, 0.0, [], 0.0), "Nobody"),
             view_people(State(0.0, 0.0, [], 0.0)))

# ---------- toggle_bought ----------
# unbought -> bought (total_spent updates)
assert_equal(
    toggle_bought(State(0.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False)], 0.0)], 0.0), "Colin", "Book"),
    view_person(State(0.0, 10.0, [Person("Colin", [Gift("Book", 10.0, True)], 0.0)], 0.0), "Colin"))
# bought -> unbought (total_spent goes back down)
assert_equal(
    toggle_bought(State(0.0, 10.0, [Person("Colin", [Gift("Book", 10.0, True)], 0.0)], 0.0), "Colin", "Book"),
    view_person(State(0.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False)], 0.0)], 0.0), "Colin"))
# only the matching gift changes
assert_equal(
    toggle_bought(State(0.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False), Gift("Pen", 5.0, False)], 0.0)], 0.0), "Colin", "Pen"),
    view_person(State(0.0, 5.0, [Person("Colin", [Gift("Book", 10.0, False), Gift("Pen", 5.0, True)], 0.0)], 0.0), "Colin"))
# gift name not found: nothing changes
assert_equal(
    toggle_bought(State(0.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False)], 0.0)], 0.0), "Colin", "Nope"),
    view_person(State(0.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False)], 0.0)], 0.0), "Colin"))

# ---------- add_gift ----------
assert_equal(
    add_gift(State(0.0, 0.0, [], 0.0), "Colin"),
    Page(State(0.0, 0.0, [], 0.0), [
        Header("Add Gift for Colin"),
        "Gift Name:",
        TextBox("name"),
        "Price:",
        TextBox("price"),
        Button("Save", save_gift, [Argument("person_name", "Colin")]),
        Button("Cancel", view_person, [Argument("person_name", "Colin")])
    ]))

# ---------- confirm_gift ----------
# adds the gift; total_spent only counts bought gifts, so it stays 0.0
assert_equal(
    confirm_gift(State(100.0, 0.0, [Person("Colin", [], 0.0)], 0.0), "Pen", 5.0, "Colin"),
    view_person(State(100.0, 0.0, [Person("Colin", [Gift("Pen", 5.0, False)], 0.0)], 0.0), "Colin"))

# ---------- save_gift ----------
# under the limit and budget: gift is added
assert_equal(
    save_gift(State(100.0, 0.0, [Person("Colin", [], 20.0)], 0.0), "Pen", 5.0, "Colin"),
    view_person(State(100.0, 0.0, [Person("Colin", [Gift("Pen", 5.0, False)], 20.0)], 0.0), "Colin"))

# exactly at the person limit is allowed (check uses >)
assert_equal(
    save_gift(State(100.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False)], 20.0)], 0.0), "Pen", 10.0, "Colin"),
    view_person(State(100.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False), Gift("Pen", 10.0, False)], 20.0)], 0.0), "Colin"))

# limit of 0 means no limit
assert_equal(
    save_gift(State(1000.0, 0.0, [Person("Colin", [], 0.0)], 0.0), "TV", 500.0, "Colin"),
    view_person(State(1000.0, 0.0, [Person("Colin", [Gift("TV", 500.0, False)], 0.0)], 0.0), "Colin"))

# over the person's limit: warning page, state unchanged
s = State(100.0, 0.0, [Person("Colin", [Gift("Book", 15.0, False)], 20.0)], 0.0)
assert_equal(
    save_gift(s, "Pen", 10.0, "Colin"),
    Page(s, [
        Header("Over Person Limit"),
        "Adding Pen ($10.0) puts Colin over their $20.0 limit.",
        Button("Add Anyway", confirm_gift, [Argument("name", "Pen"),
                                            Argument("price", 10.0),
                                            Argument("person_name", "Colin")]),
        Button("Cancel", view_person, [Argument("person_name", "Colin")])
    ]))

# over the overall budget: warning page, state unchanged
s = State(15.0, 0.0, [Person("Colin", [Gift("Book", 10.0, False)], 0.0)], 0.0)
assert_equal(
    save_gift(s, "Pen", 10.0, "Colin"),
    Page(s, [
        Header("Over Budget Warning"),
        "Adding Pen ($10.0) will put you over your budget of $15.0.",
        Button("Add Anyway", confirm_gift, [Argument("name", "Pen"),
                                            Argument("price", 10.0),
                                            Argument("person_name", "Colin")]),
        Button("Cancel", view_person, [Argument("person_name", "Colin")])
    ]))


start_server(State(0.0, 0.0, [], 0.0))
