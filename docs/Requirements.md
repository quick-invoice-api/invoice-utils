# What this is

There's a lot of invoicing utils out there which fall short of the promise of easy integration with any other system.
This should be a simple rule engine that turns an input json file containing:

- customer data
- data about the invoicing entity
- invoice header data such as the invoice currency or numbering scheme

into an output json file containing the invoiced data (amount, details, etc).
