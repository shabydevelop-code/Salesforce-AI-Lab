import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class GuideMePromptNavigationTest extends NavigationMixin(LightningElement) {
    @api recordId;
    status = 'Ready';
    generatedUrl = '';

    async handleLaunch() {
        if (!this.recordId) {
            this.status = 'No Contact recordId available';
            return;
        }

        const recordPage = {
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

        try {
            this.generatedUrl = await this[NavigationMixin.GenerateUrl](recordPage);
            this.status = 'Navigating with standard__webPage';
            this[NavigationMixin.Navigate]({
                type: 'standard__webPage',
                attributes: { url: this.generatedUrl }
            });
        } catch (error) {
            this.status = 'Navigation failed: ' + (error?.message || String(error));
        }
    }
}
