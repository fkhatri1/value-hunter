import pandas as pd, numpy as np, holoviews as hv, plotly.graph_objects as go, plotly.express as pex
from holoviews import opts, dim

hv.extension('bokeh')

expense_mapping = {
    'Federal': 'Income Tax',
    'State': 'Income Tax',
    'Medicare': 'Income Tax',
    'Social Security': 'Income Tax',
    'Groceries': 'Food',
    'Restaurants': 'Food',
    'Improvements/Maint': 'Housing',
    'Appliances': 'Housing',
    'Furniture': 'Housing',
    "Homeowner's Insurance": 'Housing',
    'Property Tax': 'Housing',
    'Home Principal': 'Housing',
    'Mortgage Interest': 'Housing',
    'Household Goods': 'Housing',
    'Electricity': 'Utilities',
    'Internet': 'Utilities',
    'Computing': 'Utilities',
    'Phone': 'Utilities',
    'Water / Trash / Sewer': 'Utilities',
    'Classes / Lessons': 'Kids',
    'Toys / Gifts': 'Kids',
    'Out of Pocket': 'Health',
    'Medical Insurance': 'Health',
    'Dental Insurance': 'Health',
    'Gym Membership': 'Fitness',
    'Equipment': 'Fitness',
    'Facilities Admission': 'Fitness',
    'Other': 'Fitness',
    'Auto Insurance': 'Transportation',
    'Yaris Maintenance': 'Transportation',
    'Sequoia Maintenance': 'Transportation',
    'Public Transit': 'Transportation',
    'Fuel': 'Transportation',
    'Parking': 'Transportation',
    'Tolls': 'Transportation',
    'Taxi': 'Transportation',
    'Vehicle Tax': 'Transportation',
    'Movie Theaters': 'Entertainment',
    'Recreation / Parks': 'Entertainment',
    'Streaming': 'Entertainment',
    'Live Shows': 'Entertainment',
    'Gaming': 'Entertainment',
    'Clothes / Shoes': 'Clothing',
    'SM Principal': 'Education',
    'SM Interest': 'Education',
    'DL Principal': 'Education',
    'DL Interest': 'Education',
    'GL Principal': 'Education',
    'GL Interest': 'Education',
    'Student Loan Principal': 'Education',
    'Student Loan Interest': 'Education',
    'Courses Tuition / Fees': 'Education',
    'Certifications': 'Education',
    'Airfare': 'Travel',
    'Hotel': 'Travel',
    'Rental Car': 'Travel',
    'Electronics / Software / Computing': 'Miscellaneous',
    'Beauty / Grooming': 'Miscellaneous',
    'Donations': 'Miscellaneous',
    'Gifts Given': 'Miscellaneous',
    'Interest/Finance Fees': 'Miscellaneous',
    'Shipping ': 'Miscellaneous',
    'Life Insurance': 'Miscellaneous',
    'Accident Insurance': 'Miscellaneous',
    'Long Term Dis. Insurance': 'Miscellaneous',
    'General Expenses': 'Miscellaneous',
    'Reconciliation': 'Miscellaneous',
    }

# expense_categories =   ["Income Tax",
#                         "Food",
#                         "Housing",
#                         "Utilities",
#                         "Kids",
#                         "Health",
#                         "Fitness",
#                         "Transportation",
#                         "Entertainment",
#                         "Education",
#                         "Travel",
#                         "Miscellaneous"
#                         ]
    
money_accounts =   ["Checking",
                    "Paypal",
                    "Venmo",
                    "Savings (Synchrony)",
                    "HSA",
                    "Savings (BlockFi)",
                    "Savings (Crypto)",
                    "Investments (Robinhood)",
                    "Income"
                    ]

def derive_data(income_df, expense_df):

    # Clear $0 rows
    income_df = income_df[income_df['amount'] != 0]
    expense_df = expense_df[expense_df['amount'] != 0]
    
    # Create empty sankey dfs
    income_sankey = pd.DataFrame({
            "Source": [],
            "Destination": [],
            "Amount": []
        })

    expense_sankey = pd.DataFrame({
            "Source": [],
            "Destination": [],
            "Amount": []
        })
    
    # Connect Subcategories to Expense Category, Remove Unnecessary Rows
    new_row = {}
    for index, row in expense_df.iterrows():
        try:
            expense_category = expense_mapping[row['expense']]
        except Exception as e:
            continue
            #raise KeyError(f"Cannot deal with expense category {row['expense']}")
            
        new_row = {
            "Source": ["Expenses"],
            "Destination": [expense_category],
            "Amount": [row['amount']]
        }
        expense_sankey = expense_sankey.append(pd.DataFrame(new_row))    
        
    # Group By
#     categories = expense_mapping.values()
#     expense_categories = set(categories)
    
#     new_row = {}
#     for category in expense_categories:
#         new_row = {
#             "Source": ["Expenses"],
#             "Destination": [category],
#             "Amount": [expense_sankey[expense_sankey['Destination']==category]['Amount'].sum()]
#         }
#         expense_sankey = expense_sankey.append(pd.DataFrame(new_row))

    expense_sankey = expense_sankey.groupby(by=["Source", "Destination"]).sum()
        
    # Connect Income Sources to Income
    new_row = {}
    for index, row in income_df.iterrows():
        new_row = {
            "Source": [row['source']],
            "Destination": ["Income"],
            "Amount": [row['amount']]
        }
        income_sankey = income_sankey.append(pd.DataFrame(new_row))  
        
    
    return (income_sankey, expense_sankey)

def get_income(df):
    ind = []
    for x in df['Destination'].values:
        if x in ['Income']:
            ind.append(True)
        else:
            ind.append(False)
           
    income_rows = df[ind]
    return income_rows

def get_expenses(df):
    ind = []
    for x in df['Source'].values:
        if x in (expense_categories + ['Expenses']):
            ind.append(True)
        else:
            ind.append(False)
                        
    expense_rows = df[ind]
    return expense_rows

def get_savings(df):
    ind = []
    for x in df['Source'].values:
        if x in (['Surplus']):
            ind.append(True)
        else:
            ind.append(False)
                        
    savings_rows = df[ind]
    return savings_rows

def get_data(income_path, expense_path):
    income, expense = derive_data(pd.read_csv(income_path, dtype={'source': str, 'amount': np.float32}), pd.read_csv(expense_path, dtype={'expense': str, 'amount': np.float32}))
    return (income, expense)


def get_sankey(df, height):
    return hv.Sankey(df, ['Source', 'Destination'], vdims='Amount').opts(label_position='outer', width=1100, height=height, cmap='Category20c', edge_color=dim('Source').str(), node_color=dim('Source').str(), node_alpha=5.0, node_width=40, node_sort=False)