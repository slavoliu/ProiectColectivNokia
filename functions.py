import ClassesOK as cls

def GetData():
    datab=cls.DataBase()
    pro=cls.Processing(datab)
    check = datab.check_collection_exists()  
    if not check:
        datab.add_data_to_database()
        datab.create_test_set_collections()
        datab.total_number_of_elements_from_db()
        pro.show_cloudification_of_each_TestSet()
    else:
        datab.run_checker()
        datab.create_test_set_collections()
        datab.total_number_of_elements_from_db()
        pro.show_cloudification_of_each_TestSet()
