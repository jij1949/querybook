import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';

import { IStoreState } from 'redux/store/types';
import {
    ExpediaResource,
    IPersonalizedSummaryDashboard,
} from 'resource/expedia';
import { Card } from 'ui/Card/Card';
import { Icon } from 'ui/Icon/Icon';
import { Link } from 'ui/Link/Link';
import { Loading } from 'ui/Loading/Loading';
import { Message } from 'ui/Message/Message';
import { Title } from 'ui/Title/Title';

import './PersonalizedCosts.scss';

export const PersonalizedCosts: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<IPersonalizedSummaryDashboard | null>(
        null
    );

    // Get the current user's username from Redux
    const username = useSelector((state: IStoreState) => {
        const uid = state.user.myUserInfo?.uid;
        return uid ? state.user.userInfoById[uid]?.username : null;
    });

    const domain = window.location.hostname;
    const skipCosts = domain === 'querybook-test.expedia.biz';

    useEffect(() => {
        if (skipCosts || !username) {
            setLoading(false);
            return;
        }

        const fetchPersonalizedCosts = async () => {
            setLoading(true);
            setError(null);

            try {
                const { data: costData } =
                    await ExpediaResource.getPersonalizedCost(username);
                setData(costData);
            } catch (err) {
                setError(
                    err instanceof Error
                        ? err.message
                        : 'Failed to fetch personalized costs'
                );
                console.error('Error fetching personalized costs:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchPersonalizedCosts();
    }, [skipCosts, username]);

    if (!username) {
        return (
            <Message message="Unable to load user information" type="error" />
        );
    }

    if (loading) {
        return <Loading />;
    }

    if (error) {
        return <Message message={error} type="error" />;
    }

    if (!data) {
        return null;
    }

    const formatCurrency = (value: number | undefined | null) =>
        new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(value ?? 0);

    const formatNumber = (value: number | undefined | null) =>
        (value ?? 0).toLocaleString();

    return (
        <div className="PersonalizedCosts">
            <Title size="large" className="PersonalizedCosts-title">
                Analytics Platform Usage
            </Title>

            <div className="PersonalizedCosts-cards-container">
                <Link
                    to="https://analytics.expedia.biz/cost/user"
                    newTab={true}
                    className="PersonalizedCosts-card-link"
                >
                    <Card className="PersonalizedCosts-card PersonalizedCosts-card-cost">
                        <div className="PersonalizedCosts-card-title">
                            Your Past 90 Days Cost
                        </div>
                        <div className="PersonalizedCosts-card-value PersonalizedCosts-card-value-large">
                            {formatCurrency(data.totalCostEstimate)}
                        </div>
                    </Card>
                </Link>

                <Link
                    to="https://analytics.expedia.biz/cost/user/querybook"
                    newTab={true}
                    className="PersonalizedCosts-card-link"
                >
                    <Card className="PersonalizedCosts-card">
                        <div className="PersonalizedCosts-card-icon">
                            <Icon name="Book" size={24} />
                        </div>
                        <div className="PersonalizedCosts-card-title">
                            Querybook DataDocs
                        </div>
                        <div className="PersonalizedCosts-card-value">
                            {formatNumber(data.numberDataDocs)}
                        </div>
                    </Card>
                </Link>

                <Link
                    to="https://analytics.expedia.biz/cost/user/trino"
                    newTab={true}
                    className="PersonalizedCosts-card-link"
                >
                    <Card className="PersonalizedCosts-card">
                        <div className="PersonalizedCosts-card-icon">
                            <Icon name="Database" size={24} />
                        </div>
                        <div className="PersonalizedCosts-card-title">
                            Trino Queries
                        </div>
                        <div className="PersonalizedCosts-card-value">
                            {formatNumber(data.numberTrinoQueries)}
                        </div>
                    </Card>
                </Link>

                <Link
                    to="https://analytics.expedia.biz/cost/user/tableau"
                    newTab={true}
                    className="PersonalizedCosts-card-link"
                >
                    <Card className="PersonalizedCosts-card">
                        <div className="PersonalizedCosts-card-icon">
                            <Icon name="LayoutGrid" size={24} />
                        </div>
                        <div className="PersonalizedCosts-card-title">
                            Tableau Extracts
                        </div>
                        <div className="PersonalizedCosts-card-value">
                            {formatNumber(data.numberExtracts)}
                        </div>
                    </Card>
                </Link>

                <Link
                    to="https://analytics.expedia.biz/cost/user/airflow"
                    newTab={true}
                    className="PersonalizedCosts-card-link"
                >
                    <Card className="PersonalizedCosts-card">
                        <div className="PersonalizedCosts-card-icon">
                            <Icon name="GitPullRequest" size={24} />
                        </div>
                        <div className="PersonalizedCosts-card-title">
                            Airflow DAGs
                        </div>
                        <div className="PersonalizedCosts-card-value">
                            {formatNumber(data.numberDags)}
                        </div>
                    </Card>
                </Link>
            </div>

            <div className="PersonalizedCosts-footer">
                <Link
                    to="https://analytics.expedia.biz/cost/user/"
                    newTab={true}
                    className="PersonalizedCosts-footer-link"
                >
                    View full details
                    <Icon name="ExternalLink" size={14} />
                </Link>
                <span className="PersonalizedCosts-footer-text">
                    Powered by{' '}
                    <Link
                        to="https://expediagroup.atlassian.net/wiki/x/3ANvFw"
                        newTab={true}
                        className="PersonalizedCosts-footer-link"
                    >
                        PUMA
                        <Icon name="ExternalLink" size={14} />
                    </Link>
                </span>
            </div>

            <hr className="PersonalizedCosts-divider" />
        </div>
    );
};
