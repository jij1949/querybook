import { shallow } from 'enzyme';
import React from 'react';

import { ErrorBoundary } from '../../ui/ErrorBoundary/ErrorBoundary';

it('renders without crashing', () => {
    shallow(<ErrorBoundary>Test</ErrorBoundary>);
});

it('resets the error state when resetKey changes', () => {
    const wrapper = shallow(
        <ErrorBoundary
            resetKey={1}
            renderError={(errorString) => <div>{errorString}</div>}
        >
            Test
        </ErrorBoundary>
    );

    wrapper.setState({
        hasError: true,
        errorString: 'Broken chart',
    });
    expect(wrapper.text()).toBe('Broken chart');

    wrapper.setProps({ resetKey: 2 });

    expect(wrapper.state('hasError')).toBe(false);
    expect(wrapper.text()).toBe('Test');
});
