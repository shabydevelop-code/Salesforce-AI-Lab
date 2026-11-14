({
    resolve: function(component, event, helper) {
        var page = component.get("v.pageReference");
        if (!page) { return; }
        var accountNumber = page.state && page.state.c__accountNumber;
        if (!accountNumber) {
            component.set("v.message", "Missing account number.");
            return;
        }
        component.set("v.message", "Looking up account...");
        var action = component.get("c.findAccount");
        action.setParams({ accountNumber: accountNumber });
        action.setCallback(this, function(response) {
            if (response.getState() === "SUCCESS") {
                var nav = $A.get("e.force:navigateToSObject");
                nav.setParams({ recordId: response.getReturnValue(), slideDevName: "detail" });
                nav.fire();
            } else {
                var errors = response.getError();
                component.set("v.message", errors && errors[0] && errors[0].message
                    ? errors[0].message : "Unable to open account.");
            }
        });
        $A.enqueueAction(action);
    }
})
