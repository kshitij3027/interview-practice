package fulfill;
public final class TestRunner { public static void main(String[] args) throws Exception { StoreTest.run(); InventoryServiceTest.run(); JsonTest.run(); System.out.println("3 test groups passed (12 assertions)"); } }
