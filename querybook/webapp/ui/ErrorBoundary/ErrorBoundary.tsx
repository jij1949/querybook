import React from 'react';

import { ErrorPage } from 'ui/ErrorPage/ErrorPage';

interface IErrorBoundaryState {
    hasError: boolean;
    errorString: string;
}

function stringifyError(errorObj: any): string {
    if (errorObj == null) {
        return 'Null error';
    } else if (errorObj instanceof Error) {
        return errorObj.message;
    }

    return JSON.stringify(errorObj);
}

interface IErrorBoundaryProps {
    renderError?: (errorString: string) => React.ReactNode;
}

export class ErrorBoundary extends React.PureComponent<
    IErrorBoundaryProps,
    IErrorBoundaryState
> {
    public readonly state = {
        hasError: false,
        errorString: '',
    };

    public componentDidCatch(errorObj, info) {
        this.setState({
            hasError: true,
            errorString: stringifyError(errorObj),
        });
    }

    public render() {
        const { hasError, errorString } = this.state;

        if (hasError) {
            if (this.props.renderError) {
                return this.props.renderError(errorString);
            }
            return (
                <ErrorPage
                    errorTitle={'Unexpected Frontend Error'}
                    errorMessage={errorString}
                />
            );
        }

        return this.props.children;
    }
}
