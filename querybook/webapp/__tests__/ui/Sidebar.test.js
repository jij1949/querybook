import { shallow } from 'enzyme';
import toJson from 'enzyme-to-json';
import React from 'react';

import { Sidebar } from '../../ui/Sidebar/Sidebar';

it('renders without crashing', () => {
    shallow(<Sidebar />);
});

describe('matches enzyme snapshots', () => {
    it('matches snapshot', () => {
        const wrapper = shallow(<Sidebar />);
        const serialized = toJson(wrapper);
        expect(serialized).toMatchSnapshot();
    });
});

describe('width control', () => {
    it('uses uncontrolled defaultSize when no size prop is given', () => {
        const resizable = shallow(<Sidebar initialWidth={320} />).find(
            'Resizable'
        );
        expect(resizable.prop('defaultSize')).toEqual({
            width: '320px',
            height: '100%',
        });
        expect(resizable.prop('size')).toBeUndefined();
    });

    it('uses controlled size and omits defaultSize when size prop is given', () => {
        const size = { width: 480, height: '100%' };
        const resizable = shallow(<Sidebar size={size} />).find('Resizable');
        expect(resizable.prop('size')).toEqual(size);
        expect(resizable.prop('defaultSize')).toBeUndefined();
    });
});
