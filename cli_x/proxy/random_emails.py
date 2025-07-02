import random
import string

def generate_random_email():
    # Common email domains
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'protonmail.com']
    
    # Common first names
    first_names = [
        'john', 'jane', 'mike', 'sarah', 'david', 'emma', 'alex', 'lisa', 'james', 'anna',
        'michael', 'sophia', 'william', 'olivia', 'robert', 'emily', 'daniel', 'ava', 'thomas', 'isabella'
    ]
    
    # Common last names
    last_names = [
        'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis', 'rodriguez', 'martinez',
        'hernandez', 'lopez', 'gonzalez', 'wilson', 'anderson', 'thomas', 'taylor', 'moore', 'jackson', 'martin'
    ]
    
    # Generate random components
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    numbers = ''.join(random.choices(string.digits, k=random.randint(1, 4)))
    year = str(random.randint(1980, 2024))
    month = str(random.randint(1, 12)).zfill(2)
    day = str(random.randint(1, 28)).zfill(2)
    domain = random.choice(domains)
    
    # Create email variations with numbers
    email_variations = [
        f"{first_name}.{last_name}@{domain}",
        f"{first_name}{last_name}{numbers}@{domain}",
        f"{first_name}_{last_name}@{domain}",
        f"{first_name[0]}{last_name}@{domain}",
        f"{first_name}{last_name[0]}@{domain}",
        f"{first_name}{year}@{domain}",
        f"{first_name}.{last_name}{numbers}@{domain}",
        f"{first_name}{last_name}{year}@{domain}",
        f"{first_name}{month}{day}@{domain}",
        f"{first_name}.{last_name}{year}@{domain}",
        f"{first_name}{last_name}_{numbers}@{domain}",
        f"{first_name}{last_name}{month}{day}@{domain}"
    ]
    
    return random.choice(email_variations)

def main():
    print("Generating 10 random email addresses:")
    print("-" * 40)
    
    # Generate and print 10 random emails
    for i in range(10):
        email = generate_random_email()
        print(f"{i+1}. {email}")

if __name__ == "__main__":
    main() 