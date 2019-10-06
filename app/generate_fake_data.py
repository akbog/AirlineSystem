from app.models import *

airline = airline(name = 'JetBlue')

airplane = airplane(id_num = 'GH712', seat_capacity = 50, airline = airline)

cust = customer(email = 'alexkbog@gmail.com', name = 'alexander', password = 'password', passport_num = '123456789', passport_expir = '12/21/2020', passport_country = 'USA', date_of_birth = '12/21/1997')

cust_address = address(customer = cust, building_num = '5002', street = 'Stonehedge', city = 'Edison', state = 'NJ', zip_code = '08820')
