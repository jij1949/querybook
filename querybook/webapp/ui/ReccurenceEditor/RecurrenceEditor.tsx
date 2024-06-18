import { Field, FormikErrors } from 'formik';
import moment from 'moment';
import * as React from 'react';
import Select from 'react-select';

import { NextRun } from 'components/NextRun/NextRun';
import {
    getMonthdayOptions,
    getRecurrenceLocalTimeString,
    getWeekdayOptions,
    getYearlyMonthOptions,
    IRecurrence,
    IRecurrenceOn,
    recurrenceToCron,
    RecurrenceType,
    recurrenceTypes,
} from 'lib/utils/cron';
import { makeReactSelectStyle } from 'lib/utils/react-select';
import { FormField } from 'ui/Form/FormField';
import { overlayRoot } from 'ui/Overlay/Overlay';
import { Tabs } from 'ui/Tabs/Tabs';
import { TimePicker } from 'ui/TimePicker/TimePicker';

import { RecurrenceEditorCronPicker } from './RecurrenceEditorCronPicker';

import './RecurrenceEditor.scss';

const recurrenceReactSelectStyle = makeReactSelectStyle(true);

interface IProps {
    recurrence: IRecurrence;
    recurrenceError?: FormikErrors<IRecurrence>;
    allowCron?: boolean;
    setRecurrence: (val: IRecurrence) => void;
}

export const RecurrenceEditor: React.FunctionComponent<IProps> = ({
    recurrence,
    recurrenceError,
    allowCron = false,
    setRecurrence,
}) => {
    const localTime = React.useMemo(
        () => getRecurrenceLocalTimeString(recurrence),
        [recurrence]
    );

    const isCron = recurrence.recurrence === 'cron';
    const isHourly = recurrence.recurrence === 'hourly';
    const isDaily = recurrence.recurrence === 'daily';
    const isWeekly = recurrence.recurrence === 'weekly';
    const isMonthly = recurrence.recurrence === 'monthly';
    const isYearly = recurrence.recurrence === 'yearly';
    const reccurenceValuesNotSet =
        (!isHourly &&
            !isDaily &&
            isWeekly &&
            (recurrence.on.dayWeek == null ||
                Object.values(recurrence.on.dayWeek).length === 0)) ||
        (isMonthly &&
            (recurrence.on.dayMonth == null ||
                Object.values(recurrence.on.dayMonth).length === 0)) ||
        (isYearly &&
            (recurrence.on.dayMonth == null ||
                recurrence.on.month == null ||
                Object.values(recurrence.on.dayMonth).length === 0 ||
                Object.values(recurrence.on.month).length === 0));

    const schedulingInfoMsgField = (
        <div className="editor-text mr12">
            NOTE: Scheduler uses UTC time. Depending on the timezone, the local
            time a DataDoc runs may appear to be different then expected.
        </div>
    );

    // Filter out cron if not allowed
    const filteredRecurrenceTypes = React.useMemo(
        () => recurrenceTypes.filter((type) => allowCron || type !== 'cron'),
        [allowCron]
    );

    const recurrenceTypeField = (
        <FormField label="Recurrence Type">
            <Field name="recurrence.recurrence">
                {({ field }) => (
                    <Tabs
                        items={filteredRecurrenceTypes}
                        selectedTabKey={field.value}
                        onSelect={(key: RecurrenceType) => {
                            const newRecurrence = {
                                ...recurrence,
                                recurrence: key,
                            };
                            if (key === 'cron') {
                                newRecurrence.cron =
                                    recurrenceToCron(recurrence);
                            }
                            if (field.value !== key) {
                                newRecurrence.on = {};
                            }
                            if (key === 'hourly' && !newRecurrence.step.hour) {
                                newRecurrence.step.hour = Number(1);
                            }
                            setRecurrence(newRecurrence);
                        }}
                        pills
                    />
                )}
            </Field>
        </FormField>
    );

    let hourSecondField: React.ReactNode;
    let datePickerField: React.ReactNode;

    if (recurrence.recurrence === 'cron') {
        datePickerField = <RecurrenceEditorCronPicker cron={recurrence.cron} />;
    } else {
        hourSecondField = (
            <FormField
                label={isHourly ? 'Minute' : 'Hour/Minute (UTC)'}
                error={recurrenceError?.hour}
            >
                <div className="flex-row">
                    {isHourly ? (
                        <>
                            <div className="editor-text mr12">
                                {'Every day, every'}
                            </div>
                            <TimePicker
                                allowEmpty={false}
                                value={moment().hour(recurrence.step.hour)}
                                showHour={true}
                                showMinute={false}
                                showSecond={false}
                                disabledHours={() => [0]}
                                hideDisabledOptions
                                format={'H'}
                                onChange={(value) => {
                                    const newRecurrence = {
                                        ...recurrence,
                                        step: { hour: value.hour() },
                                    };
                                    setRecurrence(newRecurrence);
                                }}
                            />
                            <div className="editor-text ml12 mr12">
                                {'hours at minute'}
                            </div>
                        </>
                    ) : (
                        ''
                    )}

                    <TimePicker
                        allowEmpty={false}
                        value={moment()
                            .hour(recurrence.hour)
                            .minute(recurrence.minute)}
                        minuteStep={15}
                        showHour={!(recurrence.recurrence === 'hourly')}
                        showSecond={false}
                        format={isHourly ? 'mm' : 'H:mm'}
                        onChange={(value) => {
                            const newRecurrence = {
                                ...recurrence,
                                hour: value.hour(),
                                minute: value.minute(),
                            };
                            setRecurrence(newRecurrence);
                        }}
                    />
                    <div className="editor-text ml12">
                        {isHourly ? `` : `Local Time: ${localTime}`}
                    </div>
                    <div className="editor-text ml12">
                        <div>
                            {reccurenceValuesNotSet ? (
                                'Next Run: Run Options not Set'
                            ) : (
                                <div>
                                    {'Next Run: '}
                                    <NextRun
                                        cron={recurrenceToCron(recurrence)}
                                    />
                                    {' (Local Time)'}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </FormField>
        );

        if (recurrence.recurrence === 'yearly') {
            datePickerField = (
                <>
                    <RecurrenceEditorDatePicker
                        label="Months"
                        onKey="month"
                        options={getYearlyMonthOptions()}
                        error={recurrenceError?.on}
                        recurrence={recurrence}
                        setRecurrence={setRecurrence}
                    />
                    <RecurrenceEditorDatePicker
                        label="Month Days"
                        onKey="dayMonth"
                        options={getMonthdayOptions()}
                        error={recurrenceError?.on}
                        recurrence={recurrence}
                        setRecurrence={setRecurrence}
                    />
                </>
            );
        } else if (recurrence.recurrence === 'monthly') {
            datePickerField = (
                <RecurrenceEditorDatePicker
                    label="Month Days"
                    onKey="dayMonth"
                    options={getMonthdayOptions()}
                    error={recurrenceError?.on}
                    recurrence={recurrence}
                    setRecurrence={setRecurrence}
                />
            );
        } else if (recurrence.recurrence === 'weekly') {
            datePickerField = (
                <RecurrenceEditorDatePicker
                    label="Week Days"
                    onKey="dayWeek"
                    options={getWeekdayOptions()}
                    error={recurrenceError?.on}
                    recurrence={recurrence}
                    setRecurrence={setRecurrence}
                />
            );
        }
    }

    return (
        <div className="RecurrenceEditor">
            {schedulingInfoMsgField}
            {hourSecondField}
            {recurrenceTypeField}
            {datePickerField}
        </div>
    );
};

interface IOptionType {
    value: number;
    label: string;
}
interface IDatePickerProps {
    label: string;
    onKey: string;
    options: IOptionType[];
    recurrence: IRecurrence;
    setRecurrence: (recurrence: IRecurrence) => void;
    error: FormikErrors<IRecurrenceOn>;
}

export const RecurrenceEditorDatePicker: React.FunctionComponent<
    IDatePickerProps
> = ({ label, onKey, options, error, recurrence, setRecurrence }) => {
    const formattedError = (error?.[onKey] || '').replace(
        `recurrence.on.${onKey}`,
        label
    );
    return (
        <FormField label={`Recurrence ${label}`} error={formattedError}>
            <Field
                name={`recurrence.on.${onKey}`}
                render={({ field }) => (
                    <Select<IOptionType, true>
                        menuPortalTarget={overlayRoot}
                        styles={recurrenceReactSelectStyle}
                        value={options.filter((option: { value: any }) =>
                            field.value?.includes(option.value)
                        )}
                        options={options}
                        onChange={(value) => {
                            const newRecurrence = {
                                ...recurrence,
                                on: {
                                    ...recurrence.on,
                                    [onKey]: value.map((v) => v.value),
                                },
                            };
                            setRecurrence(newRecurrence);
                        }}
                        isMulti
                    />
                )}
            />
        </FormField>
    );
};
