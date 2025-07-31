class LoanClaculator:
    def __init__(self, principal, rate, time):
        self.principal = principal
        self.rate = rate
        self.time = time

    def calculate_emi(self):
        r = self.rate / (12 * 100)  # Monthly interest rate
        n = self.time * 12  # Total number of payments
        emi = (self.principal * r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return emi

    def total_payment(self):
        emi = self.calculate_emi()
        return emi * self.time * 12

    def total_interest(self):
        return self.total_payment() - self.principal
    
    def principal_balance_after_n_installments(self, n):
        r = self.rate / (12 * 100)
        emi = self.calculate_emi()
        balance = self.principal * ((1 + r) ** n) - emi * (((1 + r) ** n - 1) / r)
        return balance

    def total_interest_paid_after_n_installments(self, n):
        emi = self.calculate_emi()
        total_paid = emi * n
        principal_paid = self.principal - self.principal_balance_after_n_installments(n)
        interest_paid = total_paid - principal_paid
        return interest_paid
    
