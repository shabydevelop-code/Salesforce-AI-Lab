@IsTest
private class IvrAccountLookupControllerTest {
    @IsTest static void findsAccount() {
        Account a = new Account(Name='IVR test', AccountNumber='IVR-TEST-001');
        insert a;
        System.assertEquals(a.Id, IvrAccountLookupController.findAccount('IVR-TEST-001'));
    }
    @IsTest static void rejectsBlankNumber() {
        try {
            IvrAccountLookupController.findAccount(' ');
            System.assert(false, 'Expected an error');
        } catch (AuraHandledException expected) {
            System.assertNotEquals(null, expected);
        }
    }
    @IsTest static void rejectsMissingAccount() {
        try {
            IvrAccountLookupController.findAccount('IVR-MISSING-999');
            System.assert(false, 'Expected an error');
        } catch (AuraHandledException expected) {
            System.assertNotEquals(null, expected);
        }
    }
    @IsTest static void rejectsDuplicates() {
        insert new List<Account>{
            new Account(Name='IVR duplicate A', AccountNumber='IVR-DUP-001'),
            new Account(Name='IVR duplicate B', AccountNumber='IVR-DUP-001')
        };
        try {
            IvrAccountLookupController.findAccount('IVR-DUP-001');
            System.assert(false, 'Expected an error');
        } catch (AuraHandledException expected) {
            System.assertNotEquals(null, expected);
        }
    }
}
