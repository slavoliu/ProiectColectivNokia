import Classes as cls

def GetData():
    db=cls.DataBase()
    if db.check_collection_exists():
        db.print_total_number_of_elements_from_db()
    else:
        db.start_DB()
        db.enter_data_from_csv_in_db()
        db.total_number_of_elements_from_db()
        db.print_total_number_of_elements_from_db()
   



