from dataclasses import dataclass
from drafter import *

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
    state.budget = float(new_budget)
    return index(state)

@route
def save_limit(state: State, new_limit: str) -> Page:
    state.per_person_limit = float(new_limit)
    return index(state)

@route
def add_reciprient(state: State) -> Page:
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
    state.recipients.append(Person(name, [], limit))
    return view_people(state)

@route
def view_people(state: State) -> Page:
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
    for person in state.recipients:
        if person.name == person_name:
            for gift in person.gifts:
                if gift.name == gift_name:
                    gift.is_bought = not gift.is_bought
    state.total_spent = total_all(state.recipients)
    return view_person(state, person_name)

@route
def add_gift(state: State, person_name: str) -> Page:
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
                return Page(state, [...])  # keep your existing warning page here
    # Check 2: the overall budget
    if total_planned(state.recipients) + price > state.budget:
        return Page(state, [...])  # keep your existing warning page here
    # No limits passed, so add the gift
    return confirm_gift(state, name, price, person_name)

@route
def confirm_gift(state: State, name: str, price: float, person_name: str) -> Page:
    for person in state.recipients:
        if person.name == person_name:
            person.gifts.append(Gift(name, price, False))
    state.total_spent = total_all(state.recipients)
    return view_person(state, person_name)

def person_planned(person: Person) -> float:
    total = 0.0
    for gift in person.gifts:
        total = total + gift.price
    return total

def total_planned(people: list[Person]) -> float:
    total = 0.0
    for person in people:
        total = total + person_planned(person)
    return total

def total_gifts(gifts: list[Gift]) -> float:
    total = 0.0
    for gift in gifts:
        if gift.is_bought:
            total = total + gift.price
    return total

def total_all(people: list[Person]) -> float:
    total = 0.0
    for person in people:
        total = total + total_gifts(person.gifts)
    return total

start_server(State(0.0, 0.0, [], 0.0))
