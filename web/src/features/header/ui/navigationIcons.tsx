import type { ReactNode } from 'react';
import AnalyticsOutlined from '@mui/icons-material/AnalyticsOutlined';
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined';
import FeedbackOutlined from '@mui/icons-material/FeedbackOutlined';
import FilePresentOutlinedIcon from '@mui/icons-material/FilePresentOutlined';
import GroupOutlined from '@mui/icons-material/GroupOutlined';
import HelpOutline from '@mui/icons-material/HelpOutline';
import InsertDriveFileOutlined from '@mui/icons-material/InsertDriveFileOutlined';
import InsertInvitationOutlined from '@mui/icons-material/InsertInvitationOutlined';
import LogoutOutlined from '@mui/icons-material/LogoutOutlined';
import MonetizationOnOutlined from '@mui/icons-material/MonetizationOnOutlined';
import MoreHorizOutlined from '@mui/icons-material/MoreHorizOutlined';
import ModeEditOutline from '@mui/icons-material/ModeEditOutline';
import PersonOutline from '@mui/icons-material/PersonOutline';
import SpaceDashboardOutlined from '@mui/icons-material/SpaceDashboardOutlined';

const iconByKey: Record<string, ReactNode> = {
  users: <PersonOutline fontSize="small" />,
  requests: <InsertDriveFileOutlined fontSize="small" />,
  feedback: <FeedbackOutlined fontSize="small" />,
  offers: <FilePresentOutlinedIcon fontSize="small" />,
  roles: <GroupOutlined fontSize="small" />,
  contact: <ModeEditOutline fontSize="small" />,
  logout: <LogoutOutlined fontSize="small" />,
  dashboard: <SpaceDashboardOutlined fontSize="small" />,
  savings: <MonetizationOnOutlined fontSize="small" />,
  plan: <InsertInvitationOutlined fontSize="small" />,
  employees: <GroupOutlined fontSize="small" />,
  economists: <GroupOutlined fontSize="small" />,
  contractors: <GroupOutlined fontSize="small" />,
  admins: <PersonOutline fontSize="small" />,
  my: <FilePresentOutlinedIcon fontSize="small" />,
  open: <InsertDriveFileOutlined fontSize="small" />,
  more: <MoreHorizOutlined fontSize="small" />,
  profile: <PersonOutline fontSize="small" />,
  guide: <HelpOutline fontSize="small" />,
  normative: <DescriptionOutlined fontSize="small" />,
  'dashboard-process': <AnalyticsOutlined fontSize="small" />,
  'dashboard-savings': <MonetizationOnOutlined fontSize="small" />,
  'dashboard-plan': <InsertInvitationOutlined fontSize="small" />,
};

export const getHeaderNavigationIcon = (key: string) => iconByKey[key] ?? <InsertDriveFileOutlined fontSize="small" />;
