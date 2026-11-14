public with sharing class IvrAccountLookupController {
    @AuraEnabled
    public static Id findAccount(String accountNumber) {
        if (String.isBlank(accountNumber) || accountNumber.length() > 40) {
            throw new AuraHandledException('Invalid account number.');
        }
        List<Account> matches = [
            SELECT Id FROM Account
            WHERE AccountNumber = :accountNumber
            WITH USER_MODE
            LIMIT 2
        ];
        if (matches.isEmpty()) {
            throw new AuraHandledException('Account not found or access denied.');
        }
        if (matches.size() > 1) {
            throw new AuraHandledException('Multiple accounts have this account number.');
        }
        return matches[0].Id;
    }
}
