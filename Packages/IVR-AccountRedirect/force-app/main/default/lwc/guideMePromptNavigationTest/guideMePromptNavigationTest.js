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

        try {
            this.generatedUrl = await this[NavigationMixin.GenerateUrl](pageReference);
            this.status = this.generatedUrl.includes('promptId')
                ? 'Generated URL contains promptId; navigating'
                : 'Generated URL does NOT contain promptId; navigating';
            // Keep the existing navigation behavior for a direct comparison.
            this[NavigationMixin.Navigate](pageReference);
        } catch (error) {
            this.status = 'GenerateUrl failed: ' + (error?.message || String(error));
        }
    }
}
