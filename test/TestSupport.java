package fulfill;
public final class TestSupport { private TestSupport() {} public static void eq(Object expected,Object actual,String message){ if(!java.util.Objects.equals(expected,actual)) throw new AssertionError(message+" expected="+expected+" actual="+actual); } public static void ok(boolean condition,String message){ if(!condition) throw new AssertionError(message); } }
