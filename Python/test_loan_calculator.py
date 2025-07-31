import pytest
from loan_emi_calculator import LoanClaculator

@pytest.fixture
def loan():
    # principal=100000, rate=10%, time=5 years
    return LoanClaculator(100000, 10, 5)

def test_calculate_emi(loan):
    emi = loan.calculate_emi()
    # Expected EMI calculated manually or from a reliable source
    assert round(emi, 2) == 2124.70

def test_total_payment(loan):
    total = loan.total_payment()
    assert round(total, 2) == round(loan.calculate_emi() * 60, 2)

def test_total_interest(loan):
    interest = loan.total_interest()
    assert round(interest, 2) == round(loan.total_payment() - loan.principal, 2)

def test_principal_balance_after_n_installments(loan):
    # After 12 installments (1 year)
    balance = loan.principal_balance_after_n_installments(12)
    assert balance < loan.principal

def test_total_interest_paid_after_n_installments(loan):
    # After 12 installments (1 year)
    interest_paid = loan.total_interest_paid_after_n_installments(12)
    assert interest_paid > 0
