import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class GuideMePromptNavigationTest extends NavigationMixin(LightningElement) {
    @api recordId;
    status = 'Ready';

    handleLaunch() {
        if (!this.recordId) {
            this.status = 'No Contact recordId available';
            return;
        }

        const pageReference = {
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: 'Contact',
                actionName: 'view'
            },
            state: {
                '0.promptId': 'GuideMe_Test_Phone'
            }
        };

        this.status = 'NavigationMixin.Navigate invoked';
        this[NavigationMixin.Navigate](pageReference);
    }
}
