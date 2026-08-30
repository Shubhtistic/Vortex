import { useTeamMembers, useRemoveMember } from '../hooks'
import Button from '@components/Button'
import type { TeamMember } from '../types'

function TeamMembersPage() {
  const { data: members, isLoading } = useTeamMembers()
  const removeMutation = useRemoveMember()

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Team Members</h2>
      </div>

      <div className="bg-white rounded-lg border border-gray-200">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                Name
              </th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                Email
              </th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                Role
              </th>
              <th className="text-right px-4 py-3 text-sm font-medium text-gray-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {members?.map((member: TeamMember) => (
              <tr key={member.id} className="border-b border-gray-100">
                <td className="px-4 py-3 text-gray-800">{member.name}</td>
                <td className="px-4 py-3 text-gray-600">{member.email}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${
                      member.role === 'admin'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {member.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeMutation.mutate(member.id)}
                  >
                    Remove
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default TeamMembersPage
